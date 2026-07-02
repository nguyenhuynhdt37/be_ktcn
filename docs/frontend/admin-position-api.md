# Đặc tả API Chức vụ (Position API Specification)

Tài liệu này cung cấp đầy đủ các endpoint, tham số request và response mẫu cho module **Chức vụ** (Position), bao gồm cả phân hệ **Quản trị (Admin CMS)** và **Trang chủ (Portal Website)**.

---

## 1. ADMIN API (CMS Quản trị)

Tất cả các endpoint trong phân hệ quản trị đều bắt đầu bằng `/api/v1/admin/positions` và yêu cầu header:
`Authorization: Bearer <token>`

### 1.1 Lấy danh sách Chức vụ (Phân trang)
*   **Method / URL**: `GET /api/v1/admin/positions`
*   **Query Parameters**:
    *   `page` (int, default=1): Trang hiện tại.
    *   `page_size` (int, default=10): Số lượng phần tử mỗi trang.
    *   `search` (string, optional): Tìm kiếm theo tên chức vụ hoặc mô tả.
    *   `is_active` (boolean, optional): Lọc theo trạng thái hoạt động (`true`/`false`).
    *   `sort_by` (string, default=`sort_order`): Trường sắp xếp (`sort_order`, `created_at`,...).
    *   `order` (string, default=`asc`): Thứ tự sắp xếp (`asc`/`desc`).
*   **Response Body (200 OK)**:
    ```json
    {
      "items": [
        {
          "id": "b45c5783-568a-4aa9-812c-653aa3dc2a95",
          "sort_order": 5,
          "is_active": true,
          "is_translated": {
            "vi": true,
            "en": true
          },
          "translations": {
            "vi": {
              "name": "Trưởng bộ môn",
              "description": "Quản lý chuyên môn của khoa",
              "is_translated": true
            },
            "en": {
              "name": "Head of Department",
              "description": "Responsible for academic management",
              "is_translated": true
            }
          },
          "name": "Trưởng bộ môn",
          "description": "Quản lý chuyên môn của khoa",
          "created_at": "2026-07-01T06:00:12Z",
          "updated_at": "2026-07-01T06:00:12Z"
        }
      ],
      "total": 1,
      "page": 1,
      "page_size": 10,
      "total_pages": 1
    }
    ```

### 1.2 Chi tiết Chức vụ
*   **Method / URL**: `GET /api/v1/admin/positions/{position_id}`
*   **Response Body (200 OK)**:
    ```json
    {
      "id": "b45c5783-568a-4aa9-812c-653aa3dc2a95",
      "sort_order": 5,
      "is_active": true,
      "is_translated": {
        "vi": true,
        "en": true
      },
      "translations": {
        "vi": {
          "name": "Trưởng bộ môn",
          "description": "Quản lý chuyên môn của khoa",
          "is_translated": true
        },
        "en": {
          "name": "Head of Department",
          "description": "Responsible for academic management",
          "is_translated": true
        }
      },
      "name": "Trưởng bộ môn",
      "description": "Quản lý chuyên môn của khoa",
      "created_at": "2026-07-01T06:00:12Z",
      "updated_at": "2026-07-01T06:00:12Z"
    }
    ```

### 1.3 Tạo Chức vụ mới
*   **Method / URL**: `POST /api/v1/admin/positions`
*   **Request Body**:
    ```json
    {
      "sort_order": 5,
      "is_active": true,
      "translations": {
        "vi": {
          "name": "Trưởng bộ môn",
          "description": "Quản lý chuyên môn của khoa"
        },
        "en": {
          "name": "Head of Department",
          "description": "Responsible for academic management"
        }
      }
    }
    ```
*   **Response Body (201 Created)**: Trả về object chức vụ tương tự API lấy chi tiết.

### 1.4 Cập nhật Chức vụ
*   **Method / URL**: `PUT /api/v1/admin/positions/{position_id}`
*   **Request Body**:
    ```json
    {
      "sort_order": 8,
      "translations": {
        "vi": {
          "name": "Trưởng bộ môn CNTT",
          "description": "Quản lý khoa CNTT"
        }
      }
    }
    ```
*   **Response Body (200 OK)**: Trả về object chức vụ tương tự API lấy chi tiết.

### 1.5 Xóa Chức vụ
*   **Method / URL**: `DELETE /api/v1/admin/positions/{position_id}`
*   **Response Body**: `204 No Content`
*   **Lưu ý**: Endpoint này sẽ chặn xóa (trả về lỗi `400 Bad Request`) nếu chức vụ đang được gắn với giảng viên nào (chưa bị xóa mềm). Payload lỗi dạng:
    ```json
    {
      "success": false,
      "error": {
        "code": "BAD_REQUEST",
        "message": "Không thể xóa chức vụ này vì đang có giảng viên đảm nhiệm",
        "details": {}
      }
    }
    ```

### 1.6 Lấy danh sách Giảng viên liên quan trước khi xóa
*   **Method / URL**: `GET /api/v1/admin/positions/staffs-to-delete`
*   **Query Parameters**:
    *   `position_ids` (string, required): Danh sách các ID chức vụ cần kiểm tra, phân tách bằng dấu phẩy (ví dụ: `position_ids=id1,id2`).
*   **Response Body (200 OK)**: Trả về danh sách giảng viên đang đảm nhiệm chức vụ này để frontend hiển thị cảnh báo:
    ```json
    [
      {
        "id": "ad41c6bc-3e82-4750-83a5-002877a572ce",
        "full_name": "Nguyễn Văn A",
        "avatar_object_key": "avatars/a.png",
        "department_name": "Công nghệ thông tin",
        "position_id": "b45c5783-568a-4aa9-812c-653aa3dc2a95"
      }
    ]
    ```

### 1.7 Lấy thống kê Chức vụ
*   **Method / URL**: `GET /api/v1/admin/positions/stats`
*   **Response Body (200 OK)**:
    ```json
    {
      "total": 8,
      "active": 8,
      "inactive": 0
    }
    ```

---

## 2. PORTAL API (Trang chủ Website)

Tất cả các endpoint trong phân hệ Portal đều công khai và không yêu cầu Token.

> [!NOTE]
> Ngôn ngữ trả về được xác định theo thứ tự ưu tiên:
> 1. Query parameter `lang=en` hoặc `lang=vi`.
> 2. Header `Accept-Language` (ví dụ: `Accept-Language: en-US,en;q=0.9`).
> 3. Mặc định là Tiếng Việt (`vi`).

### 2.1 Lấy danh sách Chức vụ hoạt động (Đã dịch và làm phẳng)
*   **Method / URL**: `GET /api/v1/portal/positions`
*   **Query Parameters**:
    *   `lang` (string, optional): Mã ngôn ngữ (`vi`/`en`).
*   **Response Body (200 OK - `lang=en`)**:
    ```json
    [
      {
        "id": "b45c5783-568a-4aa9-812c-653aa3dc2a95",
        "sort_order": 5,
        "name": "Head of Department",
        "description": "Responsible for academic management"
      }
    ]
    ```
