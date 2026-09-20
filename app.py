import streamlit as st
import os
import re
from pathlib import Path
import sys
from dotenv import load_dotenv

# Đảm bảo có thể import được các module từ src/
sys.path.append(str(Path(__file__).parent))

from src.agent import KnowledgeBaseAgent
from src.store import EmbeddingStore
from src.models import Document
from src.embeddings import (
    EMBEDDING_PROVIDER_ENV,
    GeminiEmbedder,
    LocalEmbedder,
    OpenAIEmbedder,
    _mock_embed,
)

class HeadingChunker:
    """Tách văn bản dựa vào các thẻ Heading của Markdown."""
    def chunk(self, text: str) -> list[str]:
        chunks = re.split(r'(?=\n#{1,3}\s)', text)
        return [c.strip() for c in chunks if c.strip()]

st.set_page_config(page_title="Shopee RAG Demo", page_icon="🛒", layout="wide")

@st.cache_resource
def init_system():
    # 1. Load cấu hình từ file .env
    load_dotenv(override=False)
    provider = os.getenv(EMBEDDING_PROVIDER_ENV, "mock").strip().lower()
    
    # 2. Khởi tạo Embedder
    if provider == "openai":
        try:
            embedder = OpenAIEmbedder()
        except Exception as e:
            print(f"Lỗi OpenAI: {e}")
            embedder = _mock_embed
    elif provider == "gemini":
        try:
            embedder = GeminiEmbedder()
        except Exception as e:
            print(f"Lỗi Gemini: {e}")
            embedder = _mock_embed
    elif provider == "local":
        try:
            embedder = LocalEmbedder()
        except Exception as e:
            print(f"Lỗi Local: {e}")
            embedder = _mock_embed
    else:
        embedder = _mock_embed

    # 3. Khởi tạo Vector Store
    store = EmbeddingStore(collection_name="shopee_store", embedding_fn=embedder)
    
    # 4. Load và Chunk dữ liệu từ data/ecommerce/
    data_dir = Path("data/ecommerce")
    chunker = HeadingChunker()
    docs = []
    
    if data_dir.exists():
        for file in data_dir.glob("*.md"):
            content = file.read_text(encoding="utf-8")
            chunks = chunker.chunk(content)
            for i, c in enumerate(chunks):
                if not c: continue
                docs.append(Document(
                    id=f"{file.stem}_{i}",
                    content=c,
                    metadata={"source": file.name}
                ))
    
    store.add_documents(docs)
    
    # 5. Khởi tạo LLM
    if provider == "openai":
        from openai import OpenAI
        client = OpenAI()
        
        def openai_llm(prompt: str) -> str:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Bạn là nhân viên hỗ trợ khách hàng của Shopee. Hãy trả lời câu hỏi dựa trên ngữ cảnh được cung cấp."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        llm_fn = openai_llm
    else:
        def mock_llm(prompt: str) -> str:
            context = prompt.split("Question:")[0].replace("Context:\n", "").strip()
            question = prompt.split("Question:\n")[1].split("\n\nAnswer:")[0].strip()
            
            return (f"**(Đây là Mock LLM - Chưa gọi API OpenAI/Gemini thật)**\n\n"
                    f"**Câu hỏi nhận được:** {question}\n\n"
                    f"**Dữ liệu ngữ cảnh LLM nhận được (tóm tắt):**\n```text\n{context[:300]}...\n```\n\n"
                    f"*(Nếu tích hợp LLM thật, nó sẽ đọc ngữ cảnh trên và tự động trả lời chính xác cho bạn ở đây)*")
        llm_fn = mock_llm
        
    agent = KnowledgeBaseAgent(store=store, llm_fn=llm_fn)
    return agent, store, provider

agent, store, provider = init_system()

st.title("🛒 RAG Demo: Hỏi đáp Chính sách Shopee")
st.markdown("Hệ thống tự động tìm kiếm tài liệu liên quan từ thư mục `data/ecommerce/` và trả lời câu hỏi.")

with st.sidebar:
    st.header("📊 Thống kê Vector Store")
    st.metric("Tổng số chunk đã lưu", store.get_collection_size())
    st.metric("Trình nhúng (Embedder)", provider.upper())
    st.markdown("**Các file đã nạp:**")
    
    files = [f.name for f in Path("data/ecommerce").glob("*.md")]
    if files:
        st.code("\n".join(files))
    else:
        st.warning("Không tìm thấy file nào trong data/ecommerce/")

question = st.text_input("Nhập câu hỏi của bạn (VD: Thời hạn trả hàng là bao lâu?):")

if st.button("Hỏi"):
    if question:
        with st.spinner("Đang tìm kiếm vector và xử lý..."):
            # 1. Hiển thị quá trình Search (Retrieval)
            st.subheader("🔍 Kết quả truy xuất (Retrieval)")
            results = store.search(question, top_k=3)
            
            for i, r in enumerate(results):
                with st.expander(f"Top {i+1} (Độ tương tự: {r['score']:.3f}) - Nguồn: {r['metadata'].get('source')}"):
                    st.write(r['content'])
            
            # 2. Hiển thị kết quả Agent (Generation)
            st.subheader("🤖 Trả lời của AI (Generation)")
            answer = agent.answer(question, top_k=3)
            st.info(answer)
    else:
        st.warning("Vui lòng nhập câu hỏi!")
