# Portal Category API Guide (Portal Website)

Tài liệu này hướng dẫn cách tích hợp các API danh mục (Category) dành cho Portal Website (phía Client).

---

## 1. Địa chỉ Endpoint gốc (Base URL)
Tất cả các API Portal của Category đều nằm dưới prefix:
```text
/api/v1/portal/categories
```

---

## 2. Điểm khác biệt cốt lõi so với Admin API
*   **Bảo mật & Tinh gọn**: Portal API **không expose** các trường quản trị nội bộ như `status`, `is_visible`, `is_locked`, `deleted_at`, `created_by`, `updated_by`.
*   **Không chứa `translations`**: Toàn bộ object `translations` và `is_translated` đã bị loại bỏ để giảm dung lượng payload.
*   **Tự động làm phẳng (Flatten)**: Backend tự động phân giải và gán các trường dịch thuật (`name`, `slug`, `description`, `seo_title`, `seo_description`) trực tiếp ngoài root của JSON tương ứng với ngôn ngữ hiện tại của người dùng.

---

## 3. Cơ chế Đa ngôn ngữ (Accept-Language)
Portal Client chỉ cần gửi ngôn ngữ được chọn lên qua **Header `Accept-Language`** (hoặc query param `?lang=en` / `?language=en`).
*   Nếu ngôn ngữ là `en`: Các trường `name`, `slug` ngoài root sẽ là tiếng Anh.
*   Nếu ngôn ngữ là `vi` hoặc không gửi gì: Mặc định trả về tiếng Việt.
*   Nếu ngôn ngữ được chọn chưa được dịch: Backend tự động fallback về tiếng Việt ngoài root.

---

## 4. Danh sách các API Portal

### A. Lấy cây danh mục Portal (Tree Categories)
*   **Method**: `GET`
*   **Endpoint**: `/api/v1/portal/categories/tree`
*   **Headers**: `Accept-Language: en` (hoặc `vi`)
*   **Response**: `list[PortalCategoryTreeNode]`

#### JSON Response Mẫu (Khi gửi Accept-Language: en):
```json
[
  {
    "id": "05e6ac54-0b54-44c6-bf76-39d4d05ef0c2",
    "parent_id": null,
    "thumbnail_id": null,
    "sort_order": 10,
    "is_weekly_schedule": false,
    "article_count": 8,
    
    /* --- Các trường đã được tự động dịch sang tiếng Anh ngoài root --- */
    "name": "Power and Computer Networks",
    "slug": "power-and-computer-networks",
    "description": "Department of Computer Networks",
    "seo_title": null,
    "seo_description": null,
    
    "children": []
  }
]
```

---

### B. Lấy chi tiết danh mục Portal (Detail Category)
*   **Method**: `GET`
*   **Endpoint**: `/api/v1/portal/categories/{category_id}`
*   **Response**: `PortalCategoryResponse`

#### JSON Response Mẫu:
```json
{
  "id": "05e6ac54-0b54-44c6-bf76-39d4d05ef0c2",
  "parent_id": null,
  "thumbnail_id": null,
  "sort_order": 10,
  "is_weekly_schedule": false,
  "article_count": 8,
  "name": "Power and Computer Networks",
  "slug": "power-and-computer-networks",
  "description": "Department of Computer Networks",
  "seo_title": null,
  "seo_description": null
}
```

---

### C. Lấy danh sách bài viết thuộc danh mục (Articles list)
*   **Method**: `GET`
*   **Endpoint**: `/api/v1/portal/categories/{category_slug}/articles`
*   **Response**: `PortalArticlePaginationResponse`
*   **Mô tả**: Trả về danh sách bài viết đã xuất bản thuộc danh mục này, hỗ trợ phân trang.
