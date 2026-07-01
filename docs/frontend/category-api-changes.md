# Category API Changes & Multilingual Integration Guide

Tài liệu này hướng dẫn cách tích hợp các thay đổi mới nhất của Category API vào Frontend Client (Portal & Admin), bao gồm cơ chế thống kê bài viết (`article_count`) và hiển thị đa ngôn ngữ.

---

## 1. Tổng quan các thay đổi chính của Category API

Tất cả các API liên quan đến danh mục đều đã được nâng cấp để trả về cấu trúc dữ liệu mới:
1.  **`article_count` (int)**: Số lượng bài viết đang sử dụng danh mục và chưa bị xóa mềm (`deleted_at IS NULL`).
2.  **`is_translated` (dict[str, bool])**: Trạng thái dịch của danh mục đối với từng ngôn ngữ (Ví dụ: `{"vi": true, "en": false}`).
3.  **`translations` (dict[str, dict])**: Chứa nội dung chi tiết các bản dịch được map theo mã ngôn ngữ (`vi`, `en`).
4.  **Các trường phẳng ngoài root (`name`, `slug`, `description`...)**: Đã được làm phẳng tự động theo ngôn ngữ được chọn.

---

## 2. Phân tách Đa ngôn ngữ giữa Portal Client và Admin API

Để tối ưu hóa dung lượng truyền tải dữ liệu (payload size) và bảo toàn tính năng cho Admin, Backend tự động phân loại cấu trúc JSON trả về theo ngữ cảnh của Request:

### A. API Tree (`GET /api/v1/categories/tree`)
*   **Response**: Trả về `PortalCategoryTreeNode` (Dạng cây phẳng tinh gọn).
*   **Đặc điểm**: **Loại bỏ hoàn toàn** trường `translations` và `is_translated`. Chỉ giữ lại các trường phẳng đã dịch để Portal Client vẽ menu trực tiếp và nhanh chóng.

---

### B. API Chi Tiết (`GET /api/v1/categories/{category_id}`)
API này tự động nhận biết đối tượng gọi thông qua sự hiện diện của **Query Parameter `lang` hoặc `language`**:

*   **Portal Client Call (Khi truyền `?lang=en` hoặc `?lang=vi`)**:
    *   Response trả về: `PortalCategoryResponse` (Dạng phẳng tinh gọn).
    *   **Đặc điểm**: Tự động chuyển các trường phẳng ngoài root sang tiếng Anh và **loại bỏ hoàn toàn** trường `translations` và `is_translated`.
*   **Admin Client Call (Khi gọi không truyền `lang` query)**:
    *   Response trả về: `CategoryResponse` (Dạng đầy đủ bản dịch).
    *   **Đặc điểm**: Mặc định hiển thị tiếng Việt ngoài root và **giữ nguyên** trường `translations` + `is_translated` để nạp dữ liệu vào form chỉnh sửa của Admin.

---

## 3. Cấu trúc Response mẫu cho Portal Client

Khi Portal Client gọi với query param `?lang=en` (tiếng Anh):

```json
{
  "id": "05e6ac54-0b54-44c6-bf76-39d4d05ef0c2",
  "parent_id": null,
  "thumbnail_id": null,
  "status": "ACTIVE",
  "sort_order": 0,
  "is_visible": true,
  "is_weekly_schedule": false,
  "is_locked": false,
  "article_count": 8,
  
  /* --- Các trường phẳng tự động dịch sang tiếng Anh và KHÔNG CÒN translations --- */
  "name": "Power and Computer Networks",
  "slug": "power-and-computer-networks",
  "description": "Department of Computer Networks",
  "seo_title": null,
  "seo_description": null
}
```
