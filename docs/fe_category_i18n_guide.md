# Hướng dẫn API Tạo mới, Chỉnh sửa, Chi tiết & Cây Category Đa ngôn ngữ (FE Admin)

Tài liệu này cung cấp các mẫu Request / Response API chi tiết cho lập trình viên Frontend (FE) sau khi hệ thống **loại bỏ hoàn toàn ngôn ngữ tiếng Lào (lo)**, chỉ còn hỗ trợ hai ngôn ngữ: **Tiếng Việt (vi)** và **Tiếng Anh (en)**.

---

## 📢 Thay đổi quan trọng cho Frontend
* **Không còn hỗ trợ tiếng Lào (lo)**: FE cần loại bỏ Tab tiếng Lào trên các Form tạo/sửa/xem chi tiết danh mục.
* **Chỉ hỗ trợ 2 ngôn ngữ**: Tiếng Việt (`vi`) và Tiếng Anh (`en`).
* **translations**: Object `translations` trả về chỉ bao gồm 2 keys: `"vi"` và `"en"`. Khi gửi request tạo mới / cập nhật, FE cũng chỉ gửi thông tin bản dịch cho hai ngôn ngữ này.

---

## 1. Tạo mới Category (Create)

* **Method & Endpoint**: `POST /api/v1/categories`
* **Request Payload**:
  ```json
  {
    "parent_id": null,
    "thumbnail_id": "c92df45c-6ca8-4b5d-bbe4-18f57de24743",
    "status": "PUBLISHED",
    "sort_order": 0,
    "is_visible": true,
    "is_weekly_schedule": false,
    "is_locked": false,
    "translations": {
      "vi": {
        "name": "Cơ cấu tổ chức",
        "slug": "co-cau-to-chuc",
        "description": "Mô tả tiếng Việt",
        "seo_title": "Cơ cấu tổ chức - Trường Đại học",
        "seo_description": "Mô tả SEO Việt"
      },
      "en": {
        "name": "Organizational Structure",
        "slug": "organizational-structure",
        "description": "Description in English",
        "seo_title": "SEO English",
        "seo_description": "SEO description English"
      }
    }
  }
  ```

---

## 2. Chỉnh sửa Category (Edit)

### Bước 1: Lấy thông tin cũ để điền vào Form
* **Method & Endpoint**: `GET /api/v1/categories/{id}`
* **Response**:
  ```json
  {
    "id": "92fd3d38-e4e8-4e8a-88bc-b9b26bec2572",
    "parent_id": null,
    "thumbnail_id": null,
    "status": "ACTIVE",
    "sort_order": 0,
    "is_visible": true,
    "is_weekly_schedule": false,
    "is_locked": false,
    "translations": {
      "vi": {
        "name": "Tin tức học tập",
        "slug": "tin-tuc-hoc-tap",
        "description": "Danh mục tin tức học tập",
        "seo_title": null,
        "seo_description": null
      },
      "en": {}
    }
  }
  ```

### Bước 2: Gửi Request Cập nhật
* **Method & Endpoint**: `PUT /api/v1/categories/{id}`
* **Request Payload**:
  ```json
  {
    "parent_id": null,
    "thumbnail_id": "c92df45c-6ca8-4b5d-bbe4-18f57de24743",
    "status": "PUBLISHED",
    "sort_order": 0,
    "is_visible": true,
    "is_weekly_schedule": false,
    "is_locked": false,
    "translations": {
      "vi": {
        "name": "Cơ cấu tổ chức mới",
        "slug": "co-cau-to-chuc-moi",
        "description": "Mô tả tiếng Việt mới",
        "seo_title": "Cơ cấu tổ chức mới - Trường Đại học",
        "seo_description": "Mô tả SEO Việt mới"
      },
      "en": {
        "name": "New Organizational Structure",
        "slug": "new-organizational-structure",
        "description": "New description in English",
        "seo_title": "New SEO English",
        "seo_description": "New SEO description English"
      }
    }
  }
  ```

---

## 3. Hiển thị chi tiết Category (Show/Detail)

* **Method & Endpoint**: `GET /api/v1/categories/{id}`
* **Response**:
  ```json
  {
    "id": "92fd3d38-e4e8-4e8a-88bc-b9b26bec2572",
    "parent_id": null,
    "thumbnail_id": null,
    "status": "ACTIVE",
    "sort_order": 0,
    "is_visible": true,
    "is_weekly_schedule": false,
    "is_locked": false,
    "translations": {
      "vi": {
        "name": "Tin tức học tập",
        "slug": "tin-tuc-hoc-tap",
        "description": "Danh mục tin tức học tập",
        "seo_title": null,
        "seo_description": null
      },
      "en": {}
    }
  }
  ```

---

## 4. Lấy cấu trúc cây danh mục (Get Tree Node)

* **Method & Endpoint**: `GET /api/v1/categories/tree`
* **Response**:
  ```json
  [
    {
      "id": "92fd3d38-e4e8-4e8a-88bc-b9b26bec2572",
      "parent_id": null,
      "thumbnail_id": null,
      "status": "ACTIVE",
      "sort_order": 0,
      "is_visible": true,
      "is_weekly_schedule": false,
      "is_locked": false,
      "translations": {
        "vi": {
          "name": "Tin tức học tập",
          "slug": "tin-tuc-hoc-tap",
          "description": "Danh mục tin tức học tập",
          "seo_title": null,
          "seo_description": null
        },
        "en": {}
      },
      "children": [
        {
          "id": "a823f4c9-b7e1-4c6e-9ab1-cd34ef56a782",
          "parent_id": "92fd3d38-e4e8-4e8a-88bc-b9b26bec2572",
          "thumbnail_id": null,
          "status": "ACTIVE",
          "sort_order": 10,
          "is_visible": true,
          "is_weekly_schedule": false,
          "is_locked": false,
          "translations": {
            "vi": {
              "name": "Thông báo học tập",
              "slug": "thong-bao-hoc-tap",
              "description": "Thông báo học vụ",
              "seo_title": null,
              "seo_description": null
            },
            "en": {}
          },
          "children": []
        }
      ]
    }
  ]
  ```

---

## 5. Lấy danh sách danh mục phẳng (Get List)

* **Method & Endpoint**: `GET /api/v1/categories`
* **Response**:
  ```json
  [
    {
      "id": "92fd3d38-e4e8-4e8a-88bc-b9b26bec2572",
      "parent_id": null,
      "thumbnail_id": null,
      "status": "ACTIVE",
      "sort_order": 0,
      "is_visible": true,
      "is_weekly_schedule": false,
      "is_locked": false,
      "translations": {
        "vi": {
          "name": "Tin tức học tập",
          "slug": "tin-tuc-hoc-tap",
          "description": "Danh mục tin tức học tập",
          "seo_title": null,
          "seo_description": null
        },
        "en": {}
      }
    }
  ]
  ```
