# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Trần Công Thiện
**Mã số:** 2A202602579
**Nhóm:** sunset 
**Ngày:** 20/09/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Nghĩa là góc giữa 2 vector biểu diễn câu rất nhỏ, cho thấy 2 câu đó có ngữ nghĩa hoặc từ vựng rất giống nhau/gần gũi nhau trong không gian đa chiều.

**Ví dụ có độ tương tự CAO:**
- Câu A: Tôi muốn trả hàng vì bị lỗi.
- Câu B: Sản phẩm bị hư hỏng nên tôi yêu cầu hoàn tiền.
- Tại sao tương đồng: Dù dùng từ khác nhau ("trả hàng" vs "hoàn tiền", "lỗi" vs "hư hỏng") nhưng cả hai đều mang chung một ý định khiếu nại sản phẩm lỗi để lấy lại tiền.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Tôi muốn trả hàng vì bị lỗi.
- Câu B: Tôi muốn mua một chiếc điện thoại mới.
- Tại sao khác: Một câu mang ý định khiếu nại (refund), một câu mang ý định mua sắm (purchase), nên vector của chúng sẽ nằm ở các vùng khác xa nhau.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Vì Cosine Similarity quan tâm tới hướng (ngữ nghĩa) thay vì độ lớn của vector (độ dài văn bản). Hai câu có độ dài rất khác nhau (ví dụ một câu ngắn, một đoạn dài) vẫn có thể có độ tương tự cosine cao nếu chúng nói về cùng một chủ đề, trong khi khoảng cách Euclid của chúng sẽ rất lớn.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> Độ dịch chuyển (step) = chunk_size - overlap = 500 - 50 = 450 ký tự.
> Số bước để duyệt hết 10,000 ký tự: (10,000 - 500) / 450 = 21.11 bước => Cần thêm 1 chunk cuối cùng để bọc phần dư.
> Tổng số chunk = 1 (chunk đầu) + 22 = 23 chunks.
> *Đáp án:* 23 chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Số lượng chunk sẽ tăng lên vì độ dịch chuyển (step) ngắn lại (chỉ còn 400). Ta muốn độ chồng chéo nhiều hơn để đảm bảo không một câu văn hay ý nghĩa nào bị vô tình cắt làm đôi ở ranh giới giữa 2 chunk, gây mất mát ngữ cảnh.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng Regex `(?<=[.!?])\s+|\.\n` để giữ lại dấu chấm câu bằng cơ chế lookbehind. Ngoại lệ như câu kết thúc bằng xuống dòng `.\n` cũng được xử lý. Sau đó dùng vòng lặp nhóm các câu lại theo kích thước `max_sentences_per_chunk`.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Viết hàm đệ quy `_split`, truyền vào danh sách cờ tách (separators). Tại mỗi bước, lấy separator đầu tiên (ví dụ `\n\n`) để split. Nếu đoạn văn bản sau khi split vẫn lớn hơn `chunk_size`, gọi đệ quy chính nó với các separator ưu tiên thấp hơn (như `\n`, `. `, ` `). Base case là khi chuỗi đã nhỏ hơn `chunk_size` hoặc hết separator.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Dùng một list in-memory `self._store` chứa các Dict (`record`). Để tìm kiếm, tôi lặp qua toàn bộ mảng `self._store`, tính điểm Cosine Similarity giữa vector câu hỏi và vector của tài liệu, đẩy vào một list điểm số rồi `sort(reverse=True)` để lấy ra `top_k` kết quả.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Lọc bằng cách chỉ tính Cosine Similarity nếu `metadata` của document thỏa mãn tất cả các khóa-giá trị được yêu cầu. Xóa document bằng cách gán `self._store = [doc for doc in self._store if doc['id'] != doc_id]`.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Đầu tiên gọi `self.store.search(question)`. Với các chunks nhận được, nối chúng lại bằng dấu `\n---\n` tạo thành context. Cuối cùng nhồi vào template `f"Context:\n{context}\n\nQuestion:\n{question}\n\nAnswer:"` và gửi cho LLM.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts ==============================
collected 42 items

tests/test_solution.py ..........................................        [100%]

============================== 42 passed in 1.25s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Quy định hoàn tiền | Thời gian xử lý hoàn tiền | cao | 0.82 | Đúng |
| 2 | Shopee không hỗ trợ đổi hàng | Người bán tự vận chuyển | thấp | 0.25 | Đúng |
| 3 | Thời hạn trả hàng là 15 ngày | Sản phẩm được trả trong 15 ngày | cao | 0.95 | Đúng |
| 4 | Thiết bị y tế cá nhân | Đồ bơi, đồ lót, vớ tất | thấp | 0.40 | Đúng |
| 5 | Lý do Đổi ý | Người mua không còn nhu cầu | cao | 0.88 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là "Lý do đổi ý" và "Không còn nhu cầu" không hề chia sẻ chung từ vựng nào nhưng điểm vẫn rất cao. Điều này chứng tỏ Embedding model đã thực sự hiểu "ngữ nghĩa ẩn" chứ không đơn thuần so khớp từ (keyword matching).

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Đơn hàng tự vận chuyển trả trong bao lâu? | Thời hạn đối với đơn tự vận chuyển là 15-20 ngày... | 0.89 | Có | Là 15 ngày kể từ lúc bấm đã nhận hàng. |
| 2 | Hàng nào không được đổi ý? | Danh mục tiêu biểu: Thiết bị y tế, thực phẩm, phương tiện... | 0.87 | Có | Gồm thiết bị y tế, thực phẩm tươi sống... |
| 3 | Quay video mở kiện hàng thế nào? | Cần quay liên tục, không cắt ghép, quay đủ 6 mặt... | 0.82 | Có | Bạn cần quay rõ 6 mặt kiện hàng, không cắt ghép... |
| 4 | Phạt người bán vi phạm? | Quy định xử phạt: Khóa vĩnh viễn hoặc 5 triệu. | 0.90 | Có | Người bán bị phạt 5 triệu hoặc khóa tài khoản. |
| 5 | Có được hoàn Shopee Xu không? | Hoàn Shopee Xu: có thể hoàn theo tỷ lệ tương ứng. | 0.85 | Có | Xu sẽ được hoàn theo tỷ lệ giá trị hàng trả. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Tôi học được rằng việc cắt (chunking) quá nhỏ sẽ khiến độ chính xác của câu trả lời bị giảm sút do thiếu hụt định ngữ/chủ ngữ, LLM dễ dàng bị "ảo giác" (hallucination).

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
