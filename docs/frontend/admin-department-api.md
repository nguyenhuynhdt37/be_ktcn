# Đặc tả API Bộ môn (Department API Specification)

Tài liệu này cung cấp đầy đủ các endpoint, tham số request và response mẫu cho module **Bộ môn** (Department), bao gồm cả phân hệ **Quản trị (Admin CMS)** và **Trang chủ (Portal Website)**.

---

## 1. ADMIN API (CMS Quản trị)

Tất cả các endpoint trong phân hệ quản trị đều bắt đầu bằng `/api/v1/admin/departments` và yêu cầu header:
`Authorization: Bearer <token>`

### 1.1 Lấy danh sách Bộ môn (Phân trang)
*   **Method / URL**: `GET /api/v1/admin/departments`
*   **Query Parameters**:
    *   `page` (int, default=1): Trang hiện tại.
    *   `page_size` (int, default=10): Số lượng phần tử mỗi trang.
    *   `search` (string, optional): Tìm kiếm theo tên bộ môn hoặc mô tả.
    *   `is_active` (boolean, optional): Lọc theo trạng thái hoạt động (`true`/`false`).
    *   `sort_by` (string, default=`sort_order`): Trường sắp xếp (`sort_order`, `created_at`,...).
    *   `order` (string, default=`asc`): Thứ tự sắp xếp (`asc`/`desc`).
*   **Response Body (200 OK)**:
    ```json
    {
      "items": [
        {
          "id": "e2a63c96-14ba-4b4b-9874-2aa1e1425c17",
          "thumbnail_object_key": "dept-thumb.png",
          "phone": "024-123456",
          "email": "fit@university.edu.vn",
          "website": "fit.university.edu.vn",
          "office": "Room 302, Building C1",
          "sort_order": 10,
          "is_active": true,
          "is_translated": {
            "vi": true,
            "en": true
          },
          "translations": {
            "vi": {
              "name": "Công nghệ thông tin",
              "description": "Khoa đào tạo CNTT hàng đầu",
              "slug": "cong-nghe-thong-tin",
              "is_translated": true
            },
            "en": {
              "name": "Information Technology",
              "description": "Leading IT department",
              "slug": "information-technology",
              "is_translated": true
            }
          },
          "name": "Công nghệ thông tin",
          "description": "Khoa đào tạo CNTT hàng đầu",
          "slug": "cong-nghe-thong-tin",
          "created_at": "2026-07-01T05:57:14Z",
          "updated_at": "2026-07-01T05:57:14Z"
        }
      ],
      "total": 1,
      "page": 1,
      "page_size": 10,
      "total_pages": 1
    }
    ```

### 1.2 Chi tiết Bộ môn
*   **Method / URL**: `GET /api/v1/admin/departments/{department_id}`
*   **Response Body (200 OK)**:
    ```json
    {
      "id": "e2a63c96-14ba-4b4b-9874-2aa1e1425c17",
      "thumbnail_object_key": "dept-thumb.png",
      "phone": "024-123456",
      "email": "fit@university.edu.vn",
      "website": "fit.university.edu.vn",
      "office": "Room 302, Building C1",
      "sort_order": 10,
      "is_active": true,
      "is_translated": {
        "vi": true,
        "en": true
      },
      "translations": {
        "vi": {
          "name": "Công nghệ thông tin",
          "description": "Khoa đào tạo CNTT hàng đầu",
          "slug": "cong-nghe-thong-tin",
          "is_translated": true
            },
        "en": {
          "name": "Information Technology",
          "description": "Leading IT department",
          "slug": "information-technology",
          "is_translated": true
        }
      },
      "name": "Công nghệ thông tin",
      "description": "Khoa đào tạo CNTT hàng đầu",
      "slug": "cong-nghe-thong-tin",
      "created_at": "2026-07-01T05:57:14Z",
      "updated_at": "2026-07-01T05:57:14Z"
    }
    ```

### 1.3 Tạo Bộ môn mới
*   **Method / URL**: `POST /api/v1/admin/departments`
*   **Request Body**:
    ```json
    {
      "thumbnail_object_key": "dept-thumb.png",
      "phone": "024-123456",
      "email": "fit@university.edu.vn",
      "website": "fit.university.edu.vn",
      "office": "Room 302, Building C1",
      "sort_order": 10,
      "is_active": true,
      "translations": {
        "vi": {
          "name": "Công nghệ thông tin",
          "description": "Khoa đào tạo CNTT hàng đầu"
        },
        "en": {
          "name": "Information Technology",
          "description": "Leading IT department"
        }
      }
    }
    ```
*   **Response Body (201 Created)**: Trả về object bộ môn tương tự API lấy chi tiết.

### 1.4 Cập nhật Bộ môn
*   **Method / URL**: `PUT /api/v1/admin/departments/{department_id}`
*   **Request Body**:
    ```json
    {
      "thumbnail_object_key": "dept-thumb-new.png",
      "phone": "024-999999",
      "translations": {
        "vi": {
          "name": "Khoa Công nghệ thông tin",
          "description": "Khoa đào tạo CNTT uy tín"
        }
      }
    }
    ```
*   **Response Body (200 OK)**: Trả về object bộ môn tương tự API lấy chi tiết.

### 1.5 Xóa Bộ môn
*   **Method / URL**: `DELETE /api/v1/admin/departments/{department_id}`
*   **Response Body**: `204 No Content`

### 1.6 Lấy thống kê Bộ môn
*   **Method / URL**: `GET /api/v1/admin/departments/stats`
*   **Response Body (200 OK)**:
    ```json
    {
      "total": 12,
      "active": 10,
      "inactive": 2
    }
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

### 1.8 Lấy thống kê chung (Bộ môn, Chức vụ, Giảng viên)
*   **Method / URL**: `GET /api/v1/admin/staffs/stats`
*   **Response Body (200 OK)**:
    ```json
    {
      "departments": {
        "total": 12,
        "active": 10,
        "inactive": 2
      },
      "positions": {
        "total": 8,
        "active": 8,
        "inactive": 0
      },
      "staffs": {
        "total": 45,
        "active": 40,
        "inactive": 5
      }
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

### 2.1 Lấy danh sách Bộ môn hoạt động (Đã dịch và làm phẳng)
*   **Method / URL**: `GET /api/v1/portal/departments`
*   **Query Parameters**:
    *   `lang` (string, optional): Mã ngôn ngữ (`vi`/`en`).
*   **Response Body (200 OK - `lang=en`)**:
    ```json
    [
      {
        "id": "e2a63c96-14ba-4b4b-9874-2aa1e1425c17",
        "thumbnail_object_key": "dept-thumb.png",
        "phone": "024-123456",
        "email": "fit@university.edu.vn",
        "website": "fit.university.edu.vn",
        "office": "Room 302, Building C1",
        "sort_order": 10,
        "name": "Information Technology",
        "description": "Leading IT department",
        "slug": "information-technology"
      }
    ]
    ```

### 2.2 Chi tiết Bộ môn theo Slug (Đã dịch và làm phẳng)
*   **Method / URL**: `GET /api/v1/portal/departments/{slug}`
*   **Query Parameters**:
    *   `lang` (string, optional): Mã ngôn ngữ (`vi`/`en`).
*   **Response Body (200 OK - `lang=vi`)**:
    ```json
    {
      "id": "e2a63c96-14ba-4b4b-9874-2aa1e1425c17",
      "thumbnail_object_key": "dept-thumb.png",
      "phone": "024-123456",
      "email": "fit@university.edu.vn",
      "website": "fit.university.edu.vn",
      "office": "Room 302, Building C1",
      "sort_order": 10,
      "name": "Công nghệ thông tin",
      "description": "Khoa đào tạo CNTT hàng đầu",
      "slug": "cong-nghe-thong-tin"
    }
    ```
