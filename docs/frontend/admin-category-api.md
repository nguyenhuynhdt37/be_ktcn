# Admin Category API Guide (CMS)

Tài liệu này hướng dẫn cách tích hợp các API quản lý danh mục (Category) dành riêng cho hệ thống CMS Admin.

---

## 1. Địa chỉ Endpoint gốc (Base URL)
Tất cả các API Admin của Category đều nằm dưới prefix:
```text
/api/v1/admin/categories
```

---

## 2. Danh sách các API và Cấu trúc DTO

### A. Lấy danh sách danh mục phẳng (List Categories)
*   **Method**: `GET`
*   **Endpoint**: `/api/v1/admin/categories`
*   **Response**: `list[AdminCategoryResponse]`
*   **Mô tả**: Trả về danh sách phẳng toàn bộ danh mục đang hoạt động kèm theo thống kê `article_count` và các bản dịch đa ngôn ngữ đầy đủ trong `translations`.

#### JSON Response Mẫu:
```json
[
  {
    "id": "05e6ac54-0b54-44c6-bf76-39d4d05ef0c2",
    "parent_id": null,
    "thumbnail_id": null,
    "status": "ACTIVE",
    "sort_order": 10,
    "is_visible": true,
    "is_weekly_schedule": false,
    "is_locked": false,
    "article_count": 8,
    "is_translated": {
      "vi": true,
      "en": true
    },
    "translations": {
      "vi": {
        "name": "Hệ thống và Mạng máy tính",
        "slug": "he-thong-va-mang-may-tinh",
        "description": "Bộ môn Hệ thống và Mạng máy tính"
      },
      "en": {
        "name": "Power and Computer Networks",
        "slug": "power-and-computer-networks",
        "description": "Department of Computer Networks"
      }
    }
  }
]
```

---

### B. Lấy cây danh mục Admin (Tree Categories)
*   **Method**: `GET`
*   **Endpoint**: `/api/v1/admin/categories/tree`
*   **Response**: `list[AdminCategoryTreeNode]`
*   **Mô tả**: Trả về cấu trúc cây danh mục đệ quy đầy đủ, bao gồm trạng thái translations để Admin quản lý cấu trúc cây kéo thả (drag & drop reorder).

#### JSON Response Mẫu:
```json
[
  {
    "id": "05e6ac54-0b54-44c6-bf76-39d4d05ef0c2",
    "parent_id": null,
    "status": "ACTIVE",
    "sort_order": 10,
    "is_visible": true,
    "article_count": 8,
    "translations": { ... },
    "children": [
      {
        "id": "1cfd6c41-bd84-4cb8-b34b-dbc70b427b70",
        "parent_id": "05e6ac54-0b54-44c6-bf76-39d4d05ef0c2",
        "status": "ACTIVE",
        "sort_order": 5,
        "children": []
      }
    ]
  }
]
```

---

### C. Tạo mới danh mục (Create Category)
*   **Method**: `POST`
*   **Endpoint**: `/api/v1/admin/categories`
*   **Request Body**: `CategoryCreate`
*   **Response**: `AdminCategoryResponse`

#### JSON Request Body Mẫu:
```json
{
  "parent_id": null,
  "status": "ACTIVE",
  "is_visible": true,
  "sort_order": 10,
  "translations": {
    "vi": {
      "name": "Tin tức",
      "slug": "tin-tuc",
      "description": "Danh mục tin tức"
    },
    "en": {
      "name": "News",
      "slug": "news",
      "description": "News category"
    }
  }
}
```

---

### D. Các API khác
*   `PUT /api/v1/admin/categories/{category_id}`: Cập nhật thông tin danh mục.
*   `DELETE /api/v1/admin/categories/{category_id}`: Xóa mềm danh mục.
*   `POST /api/v1/admin/categories/{category_id}/restore`: Khôi phục danh mục đã xóa mềm.
*   `PUT /api/v1/admin/categories/reorder`: Batch update kéo thả cây danh mục.
*   `GET /api/v1/admin/categories/check-slug`: Kiểm tra trùng lặp slug trong một ngôn ngữ.

---

## 4. Những lưu ý đối với Frontend Admin
*   **API Path**: Đổi toàn bộ prefix URL gọi từ `/api/v1/categories` thành `/api/v1/admin/categories`.
*   **Response Structure**: Cấu trúc JSON trả về giữ nguyên toàn bộ các trường quản trị (`translations`, `status`, `is_locked`, `is_visible`) để tương thích 100% với form CMS hiện tại.
