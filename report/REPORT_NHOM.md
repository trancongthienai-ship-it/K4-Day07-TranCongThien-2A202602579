# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** sunset
**Thành viên:**
- Trần Công Thiện - 2A202602579
- Trần Thanh Thái - 2A202602454 
- Cao Đức Hiếu - 2A202602701  
- Dương Hữu Đạt  - 2A202602544 
**Ngày:** 20/09/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Chính sách Trả Hàng & Hoàn Tiền của Sàn Thương mại điện tử Shopee (E-commerce Policy).

**Tại sao nhóm chọn chủ đề này?**
> Chúng tôi chọn chủ đề này vì đây là một trong những mảng nghiệp vụ phức tạp, nhiều quy định ràng buộc, thường xuyên gây tranh cãi và được người dùng thắc mắc rất nhiều. Ứng dụng RAG vào việc trả lời tự động các thắc mắc về trả hàng hoàn tiền sẽ mang lại giá trị thực tiễn rất cao.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | `return-refund-policy.md` | help.shopee.vn/refund | 2024-05-01 / v2.1 | 1092 | audience, source_url, retrieved_at |
| 2 | `seller-warranty-policy.md` | help.shopee.vn/warranty | 2024-05-15 / v1.5 | 967 | audience, source_url, retrieved_at |
| 3 | `shopee-thht-001.md` | help.shopee.vn/article/204305 | 2026-09-20 / v1.0 | 2500+ | audience, category, source_url |
| 4 | `shopee-thht-002.md` | help.shopee.vn/article/188931 | 2026-09-20 / v1.0 | 3000+ | audience, category, source_url |
| 5 | `shopee-thht-003.md` | help.shopee.vn/article/79465 | 2026-09-20 / v1.0 | 1200+ | audience, category, source_url |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `audience` | string | `buyer`, `seller` | Rất hữu ích để lọc đúng đối tượng: nếu là người mua hỏi thì chỉ tìm trong policy người mua. |
| `source_url` | string | `https://...` | Cho phép Agent trích dẫn lại link gốc để người dùng đọc thêm. |
| `category` | string | `refund_policy` | Lọc bớt nhiễu nếu người dùng chỉ hỏi về quy định trả hàng chứ không phải mua hàng. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| `shopee-thht-001` | FixedSizeChunker (`fixed_size`) | 12 | 225.5 | Thỉnh thoảng bị cắt ngang câu, mất nửa ý. |
| `shopee-thht-001` | SentenceChunker (`by_sentences`) | 15 | 180.2 | Trọn vẹn từng câu, nhưng có thể bị mất mối liên kết giữa các câu liên tiếp. |
| `shopee-thht-001` | RecursiveChunker (`recursive`) | 9 | 280.0 | Rất tốt, giữ nguyên được trọn vẹn cả đoạn văn vì tách theo `\n\n` trước. |

### Chiến lược của từng thành viên

**Thành viên 1 — Trần Công Thiện**
- **Loại chiến lược:** Custom Chunker (`HeadingChunker`)
- **Mô tả & lý do chọn cho chủ đề này:** Do đặc thù tài liệu E-commerce (Shopee) được trình bày bằng Markdown rất rõ ràng với các thẻ Heading (`#`, `##`), việc chia nhỏ (chunk) dựa trên các tiêu đề này sẽ giúp mỗi chunk chứa trọn vẹn một quy định cụ thể (ví dụ: một chunk chỉ nói về "THỜI HẠN GỬI YÊU CẦU").
**Thành viên 2 — Cao Đức Hiếu**
- **Loại chiến lược:** RecursiveChunker (`chunk_size=500`)
- **Mô tả & lý do chọn:** Chia đệ quy ưu tiên ngắt ở đoạn văn (`\n\n`), sau đó đến dòng (`\n`) và câu (`. `). Chiến lược này giúp giữ trọn vẹn mạch lập luận của đoạn văn, các điều khoản không bị xé vụn hoặc cắt ngang giữa câu.

**Thành viên 3 — Trần Thanh Thái**
- **Loại chiến lược:** FixedSizeChunker (`chunk_size=500, overlap=50`)
- **Mô tả & lý do chọn:** Chia cố định theo độ dài ký tự kèm cơ chế trượt (sliding window 50 ký tự). Đơn giản, đồng đều kích thước nhưng nhược điểm là dễ cắt ngang giữa một câu quy định.

**Thành viên 4 — Dương Hữu Đạt**
- **Loại chiến lược:** SentenceChunker (`max_sentences_per_chunk=3`)
- **Mô tả & lý do chọn:** Chia nhỏ theo ranh giới câu, gom 3 câu thành 1 chunk. Giúp từng câu văn nguyên vẹn ngữ pháp nhưng kích thước các chunk không đều nhau và có thể làm tách rời các câu liên quan mật thiết.
- **Code snippet:**
```python
import re

class HeadingChunker:
    """Tách văn bản dựa vào các thẻ Heading của Markdown."""
    def chunk(self, text: str) -> list[str]:
        # Tách mỗi khi gặp dấu '#' ở đầu dòng
        chunks = re.split(r'(?=\n#{1,3}\s)', text)
        return [c.strip() for c in chunks if c.strip()]
```

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Trần Công Thiện | HeadingChunker | 9/10 | Lấy trọn vẹn 1 quy định lớn, không bị mất ý. | Nếu một mục quy định quá dài, chunk sẽ bị phình to vượt mức mô hình. |
| Baseline | RecursiveChunker | 8/10 | Giữ được đoạn văn tự nhiên (paragraph). | Đôi khi tách một chủ đề (topic) ra làm 2 đoạn rời rạc. |
| Cao Đức Hiếu | RecursiveChunker (500, 50) | 8/10 | Giữ trọn vẹn từng đoạn văn (`\n\n`), overlap 50 ký tự nối tiếp ngữ cảnh mượt mà. | Đôi khi tách một quy định có nhiều đoạn thành các chunk rời rạc. |
| Trần Thanh Thái | FixedSizeChunker (500, 50) | 7/10 | Tốc độ xử lý nhanh nhất, kích thước chunk đồng đều dễ kiểm soát token. | Dễ cắt ngang câu hoặc giữa danh sách điều khoản, làm mất từ khóa quan trọng. |
| Dương Hữu Đạt | SentenceChunker (3 câu) | 7/10 | Đảm bảo nguyên vẹn cấu trúc ngữ pháp từng câu, đọc tự nhiên. | Kém hiệu quả với danh sách gạch đầu dòng không có dấu chấm câu; độ dài chunk biến thiên lớn. |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> *Chiến lược HeadingChunker là phù hợp nhất.* Với văn bản pháp lý / chính sách như Shopee, nội dung được chia mục rất rõ ràng. Cắt theo Heading giúp LLM đọc được tiêu đề mục (ngữ cảnh) cùng toàn bộ diễn giải bên dưới, giúp trả lời cực kỳ chính xác.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Đơn hàng do Người bán tự vận chuyển có thời hạn trả hàng là bao lâu? | 15 ngày từ lúc bấm đã nhận hàng; hoặc 20 ngày từ lúc lấy hàng thành công (nếu không bấm). | `shopee-thht-002` (THỜI HẠN GỬI YÊU CẦU) |
| 2 | Những mặt hàng nào không được dùng lý do "Đổi ý" để trả hàng? | Thiết bị y tế cá nhân, đồ lót, thực phẩm tươi sống, phương tiện giao thông, SIM/thẻ... | `shopee-thht-003` (DANH MỤC TIÊU BIỂU) |
| 3 | Khi quay video mở kiện hàng, cần quay những gì? | Quay liên tục không cắt ghép, rõ mã vận đơn, 6 mặt kiện hàng, quá trình mở và tình trạng sản phẩm. | `shopee-thht-004` (ĐÃ NHẬN HÀNG NHƯNG HÀNG CÓ VẤN ĐỀ - file Shopee gốc) |
| 4 | Mức phạt khi người bán vi phạm chính sách bảo hành là bao nhiêu? | Khóa tài khoản vĩnh viễn hoặc phạt tiền lên tới 5 triệu VNĐ tùy mức độ. | `seller-warranty-policy` |
| 5 | Tôi có thể được hoàn Shopee Xu nếu trả hàng do "đổi ý" không? | Có, Shopee Xu được hoàn theo phạm vi và tỷ lệ giá trị sản phẩm trả về. | `shopee-thht-002` (HOÀN MÃ GIẢM GIÁ VÀ SHOPEE XU) |

### Tổng hợp chất lượng truy xuất của nhóm

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Đơn hàng tự vận chuyển... | HeadingChunker | Có (Top 1) | Điểm cao do chunk chứa trọn vẹn tiêu đề "Thời hạn". |
| 2 | Mặt hàng không được đổi ý... | HeadingChunker | Có (Top 1) | Rất chính xác. |
| 3 | Video mở kiện cần quay gì... | RecursiveChunker | Có (Top 2) | |
| 4 | (Câu hỏi dành cho Người bán) | Lọc Metadata (`audience: seller`) | Có (Top 1) | Nếu không dùng bộ lọc, có thể ra nhầm chính sách của Người mua. |
| 5 | Hoàn Shopee Xu... | HeadingChunker | Có (Top 1) | |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> *Có, đặc biệt hữu ích ở câu 4.* Vì hệ thống có cả chính sách của Buyer (người mua) và Seller (người bán). Việc truyền `metadata_filter={"audience": "seller"}` loại bỏ ngay các file của Shopee Buyer, giúp không bị nhầm lẫn quy chế.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
- Cơ chế cắt bằng tay (Fixed, Sentence) dễ làm mất ngữ cảnh của các quy chế phức tạp.
- Sử dụng Metadata filter như 1 lớp "bảo vệ" trước khi query embeddings giúp tránh được lỗi RAG "râu ông nọ cắm cằm bà kia".

**Bài học rút ra khi so sánh trong nhóm:**
- Cùng một tài liệu, cắt bằng Recursive giúp câu trả lời tự nhiên hơn nhiều so với FixedSize. Việc áp dụng Custom HeadingChunker là tối ưu nhất với tài liệu chuẩn Markdown.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
- Nếu làm lại, nhóm sẽ tiền xử lý (preprocess) các file Markdown, thêm tên của Chính sách vào từng đoạn nhỏ (inject title vào chunk) để ngay cả khi tách lẻ, chunk vẫn mang định danh của chính sách gốc.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |
