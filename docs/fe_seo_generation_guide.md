# Hướng dẫn tích hợp AI Content Assistant (Dành cho Frontend)

Tài liệu này hướng dẫn chi tiết cách tích hợp hai tính năng mới của **AI Content Assistant** tại màn hình soạn thảo bài viết:
1.  **AI SEO Rewrite:** Viết lại & tối ưu hóa bài viết (bảo toàn hình ảnh Base64).
2.  **AI Generate from Idea:** Soạn thảo toàn bộ bài viết từ mô tả ý tưởng/dàn ý thô.

---

## 1. API 1: Viết lại bài viết (AI SEO Rewrite)

Sử dụng khi người soạn muốn AI viết lại, sửa văn phong hoặc chèn thêm từ khóa chính một cách tự nhiên vào bài viết hiện tại.

*   **Endpoint:** `POST /api/v1/admin/articles/{article_id}/seo/rewrite`
*   **Headers:** `Authorization: Bearer <token>`
*   **Request Body (`ArticleSEORewriteRequest`):**

```json
{
  "content": "<p>Chúng tôi thông báo tuyển sinh Đại học năm 2026 khoa Kỹ thuật Công nghệ.</p><img src=\"data:image/png;base64,iVBORw0...\" alt=\"Ảnh minh họa\" />",
  "focus_keyword": "tuyển sinh đại học 2026",
  "tone": "thuyết phục",
  "lang": "vi"
}
```

### Các trường dữ liệu:
*   `content` (Bắt buộc): Chuỗi HTML lấy trực tiếp từ editor (ví dụ: CKEditor/Quill). Frontend cứ gửi nguyên bản hình ảnh Base64. Backend đã có cơ chế tự động bóc tách thành placeholders để giảm dung lượng gửi đi và khôi phục lại ảnh 100% trong kết quả trả về.
*   `focus_keyword` (Tùy chọn): Từ khóa chính để AI tập trung chèn tự nhiên vào văn bản.
*   `tone` (Tùy chọn, mặc định: `"chuyên nghiệp"`): Các tone giọng hỗ trợ gợi ý:
    *   `"chuyên nghiệp"` (Văn phong trang trọng, chuẩn mực trường học)
    *   `"thuyết phục"` (Độ cuốn hút cao, kêu gọi đăng ký học)
    *   `"sáng tạo"` (Văn phong trẻ trung, thích hợp với hoạt động sinh viên)
    *   `"học thuật"` (Thích hợp cho tin tức khoa học, nghiên cứu)
*   `lang` (Tùy chọn, mặc định: `"vi"`): Ngôn ngữ của văn bản.

---

### Response Body (`ArticleSEORewriteResponse`):

```json
{
  "content": "<p>Khoa Kỹ thuật Công nghệ chính thức thông báo tuyển sinh Đại học hệ chính quy năm 2026...</p><img src=\"data:image/png;base64,iVBORw0...\" alt=\"Ảnh minh họa\" />"
}
```

*   `content`: Chuỗi HTML mới đã được viết lại, tối ưu hóa và khôi phục nguyên vẹn các hình ảnh Base64 ban đầu vào đúng vị trí.
*   **Cách tích hợp trên UI:** Đổ trực tiếp chuỗi HTML nhận được này vào editor để thay thế nội dung cũ (hoặc hiển thị modal so sánh Before/After cho người dùng bấm "Áp dụng").

---

## 2. API 2: Soạn bài từ ý tưởng (AI Generate by Idea)

Sử dụng khi người soạn chỉ có một ý tưởng thô hoặc dàn ý ngắn, muốn AI tự động viết thành một bài viết hoàn chỉnh.

*   **Endpoint:** `POST /api/v1/admin/articles/seo/generate-by-idea`
*   **Headers:** `Authorization: Bearer <token>`
*   **Request Body (`ArticleGenerateByIdeaRequest`):**

```json
{
  "idea": "Khai giảng lớp học võ cổ truyền Việt Nam miễn phí hè 2026 cho trẻ em tại trường Tiểu học Vĩnh Sơn để rèn luyện kỹ năng thoát hiểm.",
  "focus_keyword": "võ cổ truyền Việt Nam",
  "tone": "sáng tạo",
  "lang": "vi"
}
```

---

### Response Body (`ArticleGenerateByIdeaResponse`):

API trả về đầy đủ các trường thông tin cấu trúc của một bài viết:

```json
{
  "title": "Khai giảng lớp võ cổ truyền Việt Nam miễn phí hè 2026 cho trẻ em",
  "excerpt": "Trường Tiểu học Vĩnh Sơn tổ chức khai giảng lớp võ cổ truyền miễn phí hè 2026 giúp trẻ em rèn luyện kỹ năng thoát hiểm và nâng cao sức khỏe.",
  "content": "<h1>Khai giảng lớp võ cổ truyền Việt Nam miễn phí hè 2026 cho trẻ em</h1><p>Mùa hè này, các em nhỏ sẽ có cơ hội được rèn luyện sức khỏe...</p><img src=\"https://picsum.photos/800/600\" alt=\"Lớp học võ cổ truyền\" />",
  "seo_title": "Lớp học võ cổ truyền Việt Nam miễn phí hè 2026 cho trẻ em",
  "seo_description": "Đăng ký ngay lớp võ cổ truyền Việt Nam miễn phí hè 2026 tại Tiểu học Vĩnh Sơn giúp trẻ nâng cao thể lực và trang bị kỹ năng thoát hiểm tự vệ.",
  "slug": "khai-giang-lop-vo-co-truyen-viet-nam-mien-phi-he-2026-cho-tre-em"
}
```

### Cách tích hợp trên UI:
Khi người dùng bấm nút **"Soạn bài bằng AI"**:
1. Hiển thị một Modal nhập: **Ý tưởng/Dàn ý**, **Từ khóa chính (Tùy chọn)**, và chọn **Tone giọng**.
2. Khi nhấn "Bắt đầu sinh bài":
   * Hiển thị trạng thái loading (AI có thể mất khoảng **15 - 30 giây** để sinh đầy đủ bài viết).
   * Gửi dữ liệu lên API.
3. Khi nhận được kết quả trả về, tự động điền (populate) các trường tương ứng vào form soạn bài viết:
   * Trường Title -> Ô nhập Tiêu đề bài viết.
   * Trường Excerpt -> Ô nhập Tóm tắt.
   * Trường Content -> Bộ soạn thảo editor (HTML).
   * Trường Slug -> Ô nhập Slug.
   * Trường SEO Title -> Ô nhập Tiêu đề SEO.
   * Trường SEO Description -> Ô nhập Mô tả SEO.

---

## 3. API 3: Tóm tắt bài viết (AI SEO Summarize)

Sử dụng khi người soạn muốn AI tự động viết một đoạn tóm tắt bài viết ngắn gọn (dạng văn bản thuần, không HTML) từ nội dung bài viết dài hiện có để điền vào ô "Tóm tắt" (Excerpt) trên form.

*   **Endpoint:** `POST /api/v1/admin/articles/{article_id}/seo/summarize`
*   **Headers:** `Authorization: Bearer <token>`
*   **Request Body (`ArticleSummaryRequest`):**

```json
{
  "content": "<h2>Tuyển sinh Đại học năm 2026</h2><p>Khoa Kỹ thuật Công nghệ thông báo tuyển sinh đại học hệ chính quy năm 2026 với 500 chỉ tiêu...</p>",
  "max_length": 100,
  "lang": "vi"
}
```

### Các trường dữ liệu:
*   `content` (Bắt buộc): Chuỗi HTML nội dung bài viết hiện có trên editor.
*   `max_length` (Tùy chọn, mặc định: `100`): Độ dài tối đa tính bằng **số từ (words)** của đoạn tóm tắt mong muốn.
*   `lang` (Tùy chọn, mặc định: `"vi"`): Ngôn ngữ văn bản.

### Response Body (`ArticleSummaryResponse`):

```json
{
  "summary": "Khoa Kỹ thuật Công nghệ thông báo tuyển sinh Đại học hệ chính quy năm 2026 với nhiều ngành học chất lượng cao và chỉ tiêu tuyển sinh đa dạng."
}
```

*   `summary`: Chuỗi văn bản thuần túy (không chứa thẻ HTML, không markdown). Đây là một câu hoặc đoạn văn hoàn chỉnh, kết thúc bằng dấu chấm câu đầy đủ, không bị cắt dở dang và không chứa dấu ba chấm (...) ở cuối.
*   **Cách tích hợp trên UI:** Đặt nút **"Tóm tắt bằng AI"** ngay bên cạnh hoặc bên dưới ô nhập liệu "Tóm tắt" (Excerpt). Khi có kết quả, đổ trực tiếp chuỗi `summary` này vào ô nhập liệu đó.

---

## 4. Khuyến nghị UI/UX cho Frontend

1.  **Trạng thái Chờ (Loading state):** Do mô hình AI cần xử lý và sinh ra văn bản, thời gian phản hồi trung bình sẽ từ **5s - 25s**. Frontend cần thiết kế loader chuyên dụng.
2.  **Cảnh báo chống spam:** Vui lòng disable nút bấm gửi yêu cầu trong quá trình API đang load để tránh việc người soạn bấm liên tục gửi nhiều request AI trùng lặp gây quá tải hệ thống.

