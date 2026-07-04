# Hướng dẫn tích hợp Frontend: AI SEO Assistant cho Article Module

Tài liệu này cung cấp đặc tả chi tiết về API, cấu trúc Request/Response và hướng dẫn thiết kế giao diện (UI/UX) cho đội ngũ phát triển Frontend khi tích hợp tính năng **AI SEO Assistant** vào màn hình soạn thảo bài viết.

---

## 1. Thông tin chung về API Phân tích SEO

*   **Endpoint:** `POST /api/v1/admin/articles/{article_id}/seo/analyze`
*   **Mô tả:** Thực hiện phân tích SEO cho bài viết theo thời gian thực. API kết hợp Rule Engine tĩnh để chấm điểm và gọi AI Hub (Gemini) để viết gợi ý tối ưu và phát hiện từ khóa, liên kết nội bộ.
*   **Xác thực:** Yêu cầu Header `Authorization: Bearer <token>` (phân quyền Admin).
*   **Tham số đường dẫn (Path Parameter):**
    *   `article_id`: UUID của bài viết (Nếu là bài viết mới chưa lưu, FE truyền một UUID ngẫu nhiên hoặc UUID nháp được sinh ở client).

---

## 2. Đặc tả Dữ liệu API (Request & Response)

### A. Request Body
Frontend gửi dữ liệu thô đang chỉnh sửa trên Form soạn thảo (chưa cần nhấn lưu xuống Database) để phân tích real-time.

```json
{
  "title": "Tuyển sinh Đại học năm 2026 khoa Kỹ thuật Công nghệ",
  "content": "<h2>Thông tin chung về tuyển sinh</h2><p>Khoa Kỹ thuật Công nghệ thông báo tuyển sinh đại học hệ chính quy năm 2026. Đây là cơ hội lớn cho các học sinh đam mê công nghệ.</p><img src=\"data:image/png;base64,iVBORw0KGgoAAAANS...\" alt=\"Ảnh khoa\" /><img src=\"https://ktcn.edu.vn/images/featured.jpg\" /><a href=\"/portal/categories/tuyen-sinh\">Xem thêm danh mục tuyển sinh</a>",
  "excerpt": "Thông tin chi tiết về tuyển sinh Đại học năm 2026 của khoa Kỹ thuật Công nghệ.",
  "seo_title": "Tuyển sinh Đại học năm 2026 khoa Kỹ thuật Công nghệ - Đăng ký ngay",
  "seo_description": "Khoa Kỹ thuật Công nghệ thông báo tuyển sinh đại học năm 2026 với nhiều chỉ tiêu hấp dẫn. Đăng ký ngay hôm nay để nhận học bổng.",
  "focus_keyword": "tuyển sinh đại học",
  "thumbnail_object_key": "article/thumbnail/featured.jpg",
  "slug": "tuyen-sinh-dai-hoc-nam-2026-khoa-ky-thuat-cong-nghe",
  "lang": "vi"
}
```

*Lưu ý về trường `content`:* Cứ gửi mã HTML nguyên bản từ Rich Text Editor (ví dụ: CKEditor/Quill). Backend đã có cơ chế tự động lọc và loại bỏ toàn bộ dữ liệu Base64 Image, CSS inline, script để tối ưu dung lượng token.

---

### B. Response Body (JSON)
API trả về phân tích đầy đủ từ Rule Engine tĩnh và AI Hub:

```json
{
  "score": 65,
  "status": "warning",
  "issues": [
    {
      "type": "missing_featured_image",
      "message": "Bài viết chưa có ảnh đại diện (Featured Image)."
    },
    {
      "type": "title_too_long",
      "message": "Tiêu đề SEO quá dài (66 ký tự). Độ dài tối ưu là 40 - 65 ký tự để tránh bị cắt bớt trên Google."
    },
    {
      "type": "missing_image_alt",
      "message": "Có 1/2 hình ảnh trong bài viết chưa được điền thẻ mô tả Alt text."
    },
    {
      "type": "content_too_short",
      "message": "Bài viết quá ngắn (58 từ). Nên viết tối thiểu 300 từ để được Google đánh giá cao."
    },
    {
      "type": "keyword_missing_heading",
      "message": "Từ khóa chính 'tuyển sinh đại học' chưa xuất hiện ở bất kỳ tiêu đề phụ H2/H3 nào."
    },
    {
      "type": "missing_external_link",
      "message": "Thiếu liên kết ngoài. Nên thêm liên kết tham chiếu tới các trang uy tín (như Bộ GDĐT, v.v.)."
    }
  ],
  "suggestions": [
    "Mở rộng nội dung bài viết lên tối thiểu 300 từ để cung cấp thông tin chi tiết hơn về chương trình đào tạo, cơ hội nghề nghiệp...",
    "Thêm ảnh đại diện (Featured Image) hấp dẫn và có liên quan đến chủ đề tuyển sinh.",
    "Kiểm tra và điền đầy đủ thẻ mô tả Alt text cho tất cả hình ảnh trong bài viết.",
    "Tối ưu lại tiêu đề SEO để có độ dài trong khoảng 45-65 ký tự.",
    "Thêm liên kết ngoài (external links) đến các trang web uy tín."
  ],
  "generated_seo_title": "Tuyển sinh Đại học 2026 Khoa Kỹ thuật Công nghệ: Cơ hội vàng!",
  "generated_meta_description": "Khoa Kỹ thuật Công nghệ thông báo tuyển sinh đại học 2026. Khám phá các ngành Công nghệ thông tin, Kỹ thuật điện tử, Cơ điện tử cùng cơ hội học bổng hấp dẫn. Đăng ký ngay!",
  "focus_keywords": [
    "tuyển sinh khoa kỹ thuật công nghệ",
    "ngành công nghệ thông tin",
    "tuyển sinh 2026"
  ],
  "internal_links": [
    {
      "anchor_text": "tuyển sinh đại học hệ chính quy năm 2026",
      "url": "/portal/tags/tuyen-sinh-2026",
      "reason": "Liên kết đến trang tổng hợp các tin tức tuyển sinh năm 2026, giúp người đọc tìm thêm thông tin."
    },
    {
      "anchor_text": "Công nghệ thông tin",
      "url": "/portal/departments/khoa-cntt",
      "reason": "Liên kết đến trang giới thiệu về Khoa Công nghệ thông tin, cung cấp thông tin chi tiết về ngành học này."
    }
  ],
  "google_preview": {
    "title": "Tuyển sinh Đại học năm 2026 khoa Kỹ thuật Công nghệ - Đăng ký ngay",
    "url": "https://ktcn.edu.vn/portal/articles/tuyen-sinh-dai-hoc-nam-2026-khoa-ky-thuat-cong-nghe",
    "description": "Khoa Kỹ thuật Công nghệ thông báo tuyển sinh đại học năm 2026 với nhiều chỉ tiêu hấp dẫn. Đăng ký ngay hôm nay để nhận học bổng."
  }
}
```

---

## 3. Hướng dẫn thiết kế Giao diện (UI/UX) cho FE

### A. Vị trí hiển thị Panel SEO Assistant
Bổ sung một panel ở sidebar bên phải màn hình soạn thảo bài viết (hoặc một Tab riêng biệt bên cạnh Tab "Nội dung" / "Cài đặt").
*   Tên Panel: **Trợ lý AI SEO** (AI SEO Assistant).
*   Trạng thái Loading: Hiển thị spinner kèm chữ `"AI đang phân tích bài viết của bạn..."` khi gọi API (thời gian xử lý trung bình từ 3 - 6 giây).

### B. Vòng tròn điểm số SEO (SEO Score)
*   Hiển thị điểm số `score` lớn từ `0 - 100` dạng Radial Progress Circle.
*   Màu sắc động theo trường `status`:
    *   `good` (score >= 80): Màu xanh lá (`#10B981` hoặc `success`).
    *   `warning` (score 50 - 79): Màu vàng/cam (`#F59E0B` hoặc `warning`).
    *   `error` (score < 50): Màu đỏ (`#EF4444` hoặc `danger`).

### C. Danh sách lỗi kỹ thuật (Rule Check List)
Hiển thị danh sách các `issues` từ Rule Engine dưới dạng Collapsible / Accordion để người soạn bài biết chính xác cần sửa gì.
*   Mỗi lỗi có icon cảnh báo tương ứng (icon cảnh báo đỏ cho các lỗi nghiêm trọng như thiếu tiêu đề, thiếu slug, và icon vàng cho các khuyến nghị phụ).
*   Ví dụ:
    *   ⚠️ *Tiêu đề SEO quá dài (66 ký tự)...*
    *   ❌ *Bài viết chưa có ảnh đại diện.*

### D. Gợi ý từ AI (AI Suggestions)
Hiển thị các đề xuất cải thiện văn phong, phân bổ từ khóa từ AI dưới dạng các thẻ (Card) hoặc danh sách bullet chỉn chu.

### E. Gợi ý Tối ưu Tiêu đề & Mô tả SEO (Apply Suggestions)
Hiển thị song song thông tin AI đề xuất:
1.  **AI SEO Title:** `generated_seo_title`
2.  **AI Meta Description:** `generated_meta_description`
*   Bổ sung nút **"Áp dụng gợi ý" (Apply)** bên cạnh mỗi trường.
*   Khi người dùng click **Apply**, Frontend tự động copy giá trị tương ứng điền vào ô nhập liệu `SEO Title` / `SEO Description` tương ứng của form soạn thảo và cập nhật ngay lập tức phần **Google Preview**.

### F. Google Search Preview (Thời gian thực)
Mô phỏng chính xác giao diện kết quả tìm kiếm của Google:
*   Tiêu đề màu xanh dương chuẩn link (lấy từ form, nếu form trống lấy gợi ý từ AI).
*   Đường dẫn URL màu xanh lá cây nhạt hoặc xám.
*   Mô tả màu xám tối / đen.
*   Cập nhật trực tiếp (real-time) khi người dùng gõ vào form hoặc khi bấm Apply gợi ý AI.

### G. Gợi ý liên kết nội bộ (Internal Link Suggestions)
Hiển thị danh sách gợi ý liên kết nội bộ `internal_links`.
*   Mỗi dòng gồm: Cụm từ cần gắn link (`anchor_text`), đường dẫn đề xuất (`url`), và lý do đề xuất (`reason`).
*   Bổ sung nút **Copy Link** hoặc **Chèn nhanh** để người dùng có thể dễ dàng dán liên kết vào editor soạn thảo.

---

## 4. Quy tắc tối ưu Hiệu năng & Tránh spam API (Spam Prevention)

*   **Không gọi tự động khi gõ chữ:** Không kích hoạt API phân tích SEO tự động liên tục mỗi khi gõ phím để tránh làm chậm hệ thống và lãng phí token AI Hub.
*   **Cơ chế kích hoạt:**
    1.  Khuyên dùng thiết kế nút bấm chủ động: **"Phân tích SEO với AI"** (Chỉ gọi API khi người dùng nhấn nút này).
    2.  Hoặc tự động gọi sau khi người soạn bài dừng gõ từ **5 - 10 giây** (Debounce ở mức cao) và có sự thay đổi lớn về mặt ký tự (trên 100 từ).
