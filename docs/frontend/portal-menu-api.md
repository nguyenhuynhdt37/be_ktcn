# Hướng dẫn tích hợp Frontend - Module Menu (Đa ngôn ngữ & Phân tách API)

Tài liệu này hướng dẫn cách gọi API của module Menu sau khi refactor tách biệt tầng Admin CMS và Portal Client, tích hợp cơ chế đa ngôn ngữ (i18n).

---

## 1. ADMIN API (CMS Quản trị)

Tất cả các API quản trị đều nằm dưới prefix: `/api/v1/admin/menus`
Yêu cầu header: `Authorization: Bearer <token>`

### 1.1. Tạo mục Menu mới (Create MenuItem)
*   **Method / URL**: `POST /api/v1/admin/menus/{menu_id}/items`
*   **Request Body**:
    ```json
    {
      "parent_id": null, // UUID hoặc null nếu là root
      "target_type": "CATEGORY", // CATEGORY, ARTICLE, PAGE, DEPARTMENT, MODULE, EXTERNAL_LINK hoặc null
      "target_id": "05e6ac54-0b54-44c6-bf76-39d4d05ef0c2", // UUID tương ứng hoặc null
      "external_url": null, // String (chỉ dùng khi target_type là EXTERNAL_LINK)
      "open_in_new_tab": false,
      "sort_order": 10,
      "is_visible": true,
      "translations": {
        "vi": {
          "title": "Đào tạo"
        },
        "en": {
          "title": "Academics"
        }
      }
    }
    ```
*   **Response Body (201 Created)**:
    ```json
    {
      "id": "aad296ac-a9ca-4b2c-ad56-90adb1c487b3",
      "menu_id": "a21d39e5-427d-449a-a858-d28b041a44c4",
      "parent_id": null,
      "target_type": "CATEGORY",
      "target_id": "05e6ac54-0b54-44c6-bf76-39d4d05ef0c2",
      "target_info": null,
      "external_url": null,
      "open_in_new_tab": false,
      "depth": 1,
      "sort_order": 10,
      "is_visible": true,
      "has_link": true,
      "title": "Đào tạo", // Trả về tiêu đề ngôn ngữ mặc định (vi) ở Admin
      "translations": {
        "vi": {
          "title": "Đào tạo",
          "is_translated": true
        },
        "en": {
          "title": "Academics",
          "is_translated": true
        }
      },
      "is_translated": {
        "vi": true,
        "en": true
      }
    }
    ```

### 1.2. Lấy Cây Menu Admin (Get Tree)
*   **Method / URL**: `GET /api/v1/admin/menus/{menu_id}/tree`
*   **Response Body (200 OK)**:
    ```json
    {
      "id": "a21d39e5-427d-449a-a858-d28b041a44c4",
      "name": "Header Main Menu",
      "code": "header_main",
      "description": "Menu chính",
      "is_active": true,
      "items": [
        {
          "id": "aad296ac-a9ca-4b2c-ad56-90adb1c487b3",
          "menu_id": "a21d39e5-427d-449a-a858-d28b041a44c4",
          "parent_id": null,
          "target_type": "CATEGORY",
          "target_id": "05e6ac54-0b54-44c6-bf76-39d4d05ef0c2",
          "target_info": {
            "title": "Tin học Đại cương",
            "slug": "tin-hoc-dai-cuong"
          },
          "external_url": null,
          "open_in_new_tab": false,
          "depth": 1,
          "sort_order": 10,
          "is_visible": true,
          "has_link": true,
          "title": "Đào tạo",
          "translations": {
            "vi": { "title": "Đào tạo", "is_translated": true },
            "en": { "title": "Academics", "is_translated": true }
          },
          "is_translated": { "vi": true, "en": true },
          "children": []
        }
      ]
    }
    ```

### 1.3. Cập nhật Menu Item (Update MenuItem)
*   **Method / URL**: `PUT /api/v1/admin/menus/{menu_id}/items/{item_id}`
*   **Request Body**:
    ```json
    {
      "translations": {
        "vi": {
          "title": "Chương trình đào tạo"
        },
        "en": {
          "title": "Academic Programs"
        }
      }
    }
    ```
*   **Response Body (200 OK)**:
    ```json
    {
      "id": "aad296ac-a9ca-4b2c-ad56-90adb1c487b3",
      "menu_id": "a21d39e5-427d-449a-a858-d28b041a44c4",
      "parent_id": null,
      "title": "Chương trình đào tạo",
      "translations": {
        "vi": { "title": "Chương trình đào tạo", "is_translated": true },
        "en": { "title": "Academic Programs", "is_translated": true }
      }
      // ...các trường cấu hình khác giữ nguyên...
    }
    ```

### 1.4. Kéo thả Menu Items (Batch Reorder)
*   **Method / URL**: `PUT /api/v1/admin/menus/{menu_id}/items/reorder`
*   **Request Body**:
    ```json
    {
      "items": [
        {
          "id": "aad296ac-a9ca-4b2c-ad56-90adb1c487b3",
          "parent_id": null,
          "sort_order": 10
        },
        {
          "id": "cdfa087f-0e8a-4bc3-b7b6-0498d309156f",
          "parent_id": "aad296ac-a9ca-4b2c-ad56-90adb1c487b3", // đẩy vào làm con
          "sort_order": 20
        }
      ]
    }
    ```
*   **Response Body (200 OK)**:
    ```json
    {
      "success": true,
      "reordered": 2
    }
    ```

---

## 2. PORTAL API (Website công khai)

Tất cả các API Portal nằm dưới prefix: `/api/v1/portal/menus`
Không yêu cầu token xác thực.
Hỗ trợ i18n tự động: Nhận diện qua header `Accept-Language` (ví dụ: `en`) hoặc query parameter `?lang=en` (hoặc `?language=en`).

### 2.1. Lấy Cây Menu phẳng đã dịch (Get Portal Tree)
*   **Method / URL**: `GET /api/v1/portal/menus/{code}/tree?lang=en`
*   **Response Body (200 OK - Đã được làm phẳng và dịch tự động)**:
    ```json
    {
      "id": "a21d39e5-427d-449a-a858-d28b041a44c4",
      "name": "Header Main Menu",
      "code": "header_main",
      "description": "Menu chính",
      "is_active": true,
      "items": [
        {
          "id": "aad296ac-a9ca-4b2c-ad56-90adb1c487b3",
          "menu_id": "a21d39e5-427d-449a-a858-d28b041a44c4",
          "parent_id": null,
          "target_type": "CATEGORY",
          "target_id": "05e6ac54-0b54-44c6-bf76-39d4d05ef0c2",
          "target_info": {
            "title": "Computer Networks", // Target info cũng được dịch tự động nếu có
            "slug": "computer-networks"
          },
          "external_url": null,
          "open_in_new_tab": false,
          "depth": 1,
          "sort_order": 10,
          "is_visible": true,
          "has_link": true,
          
          /* --- Trường được làm phẳng và tự động dịch ngoài root --- */
          "title": "Academic Programs", 
          
          "children": [
            {
              "id": "cdfa087f-0e8a-4bc3-b7b6-0498d309156f",
              "menu_id": "a21d39e5-427d-449a-a858-d28b041a44c4",
              "parent_id": "aad296ac-a9ca-4b2c-ad56-90adb1c487b3",
              "title": "Information Technology", // dịch tự động
              "children": []
              // ... các trường phẳng khác ...
            }
          ]
        }
      ]
    }
    ```
