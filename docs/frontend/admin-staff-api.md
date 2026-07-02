# Đặc tả API Giảng viên (Staff API Specification)

Tài liệu này cung cấp đầy đủ các endpoint, tham số request và response mẫu cho module **Giảng viên** (Staff / Cán bộ), bao gồm cả phân hệ **Quản trị (Admin CMS)** và **Trang chủ (Portal Website)**.

---

## 1. ADMIN API (CMS Quản trị)

Tất cả các endpoint trong phân hệ quản trị đều bắt đầu bằng `/api/v1/admin/staffs` và yêu cầu header:
`Authorization: Bearer <token>`

### 1.1 Lấy danh sách Giảng viên (Phân trang)
*   **Method / URL**: `GET /api/v1/admin/staffs`
*   **Query Parameters**:
    *   `page` (int, default=1): Trang hiện tại.
    *   `page_size` (int, default=10): Số lượng phần tử mỗi trang.
    *   `search` (string, optional): Tìm kiếm theo tên giảng viên, email hoặc số điện thoại.
    *   `department_id` (string, optional): Lọc theo ID bộ môn (UUID).
    *   `position_id` (string, optional): Lọc theo ID chức vụ (UUID).
    *   `is_active` (boolean, optional): Lọc theo trạng thái hoạt động (`true`/`false`).
    *   `sort_by` (string, default=`sort_order`): Trường sắp xếp (`sort_o    {
      "items": [
        {
          "id": "ad41c6bc-3e82-4750-83a5-002877a572ce",
          "department_id": "4ecf0178-26d8-4a48-9fef-1fc8daad0734",
          "position_id": "b45c5783-568a-4aa9-812c-653aa3dc2a95",
          "academic_title_id": "7430f8c0-bec9-417d-8d17-6d1073a3d4fa",
          "degree_id": "c17f1648-ebc9-460e-96a0-026f94e082b5",
          "full_name": "Nguyễn Văn A",
          "english_name": "A Nguyen Van",
          "slug": "nguyen-van-a",
          "avatar_object_key": "avatars/a.png",
          "email": "anv@university.edu.vn",
          "phone": "0987654321",
          "website": "anv.blog",
          "office": "Room 501, Building B1",
          "sort_order": 5,
          "is_active": true,
          "is_translated": {
            "vi": true,
            "en": true
          },
          "translations": {
            "vi": {
              "biography": "Quá trình công tác dài hạn...",
              "research_interests": "Trí tuệ nhân tạo, Big Data",
              "is_translated": true
            },
            "en": {
              "biography": "Long working history...",
              "research_interests": "Artificial Intelligence, Big Data",
              "is_translated": true
            }
          },
          "academic_title": "Phó giáo sư",
          "degree": "Tiến sĩ",
          "biography": "Quá trình công tác dài hạn...",
          "research_interests": "Trí tuệ nhân tạo, Big Data",
          "created_at": "2026-07-01T06:00:12Z",
          "updated_at": "2026-07-01T06:00:12Z",
          "department": {
            "id": "4ecf0178-26d8-4a48-9fef-1fc8daad0734",
            "thumbnail_object_key": "fit-thumb.png",
            "phone": "024-123456",
            "email": "fit@university.edu.vn",
            "website": "fit.university.edu.vn",
            "office": "Room 302",
            "sort_order": 10,
            "is_active": true,
            "name": "Công nghệ thông tin",
            "description": "Khoa CNTT"
          },
          "position": {
            "id": "b45c5783-568a-4aa9-812c-653aa3dc2a95",
            "sort_order": 5,
            "is_active": true,
            "name": "Trưởng bộ môn"
          }
        }
      ],
      "total": 1,
      "page": 1,
      "page_size": 10,
      "total_pages": 1
    }
    ```

### 1.2 Chi tiết Giảng viên
*   **Method / URL**: `GET /api/v1/admin/staffs/{staff_id}`
*   **Response Body (200 OK)**: Trả về object giảng viên tương tự cấu trúc trong list (có chứa thông tin `department`, `position` chi tiết).

### 1.3 Tạo Giảng viên mới
*   **Method / URL**: `POST /api/v1/admin/staffs`
*   **Request Body**:
    ```json
    {
      "department_id": "4ecf0178-26d8-4a48-9fef-1fc8daad0734",
      "position_id": "b45c5783-568a-4aa9-812c-653aa3dc2a95",
      "academic_title_id": "7430f8c0-bec9-417d-8d17-6d1073a3d4fa",
      "degree_id": "c17f1648-ebc9-460e-96a0-026f94e082b5",
      "full_name": "Nguyễn Văn A",
      "english_name": "A Nguyen Van",
      "avatar_object_key": "avatars/a.png",
      "email": "anv@university.edu.vn",
      "phone": "0987654321",
      "website": "anv.blog",
      "office": "Room 501, Building B1",
      "sort_order": 5,
      "is_active": true,
      "translations": {
        "vi": {
          "biography": "Quá trình công tác dài hạn...",
          "research_interests": "Trí tuệ nhân tạo, Big Data"
        },
        "en": {
          "biography": "Long working history...",
          "research_interests": "Artificial Intelligence, Big Data"
        }
      }
    }
    ```
*   **Response Body (201 Created)**: Trả về object giảng viên tương tự chi tiết.

### 1.4 Cập nhật Giảng viên
*   **Method / URL**: `PUT /api/v1/admin/staffs/{staff_id}`
*   **Request Body**:
    ```json
    {
      "office": "Room 602, Building B1",
      "academic_title_id": "ccd2449c-2ed9-4d39-86f8-f59fa33282bb",
      "degree_id": "5c93a214-0e7e-4384-bab8-ca403e3ac4ae",
      "translations": {
        "vi": {
          "biography": "Lý lịch khoa học chi tiết"
        }
      }
    }
    ```
*   **Response Body (200 OK)**: Trả về object giảng viên tương tự chi tiết.

### 1.5 Xóa Giảng viên
*   **Method / URL**: `DELETE /api/v1/admin/staffs/{staff_id}`
*   **Response Body**: `204 No Content`

### 1.6 Lấy thống kê chung (Bộ môn, Chức vụ, Giảng viên)
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

### 1.7 Lấy danh sách Học hàm & Học vị (Dành cho bộ lọc & dropdown form)
CMS Admin gọi các API này để lấy danh sách hiển thị trên dropdown hoặc bộ lọc:

#### A. Danh sách Học hàm
*   **Method / URL**: `GET /api/v1/admin/academic-titles`
*   **Response Body (200 OK)**:
    ```json
    [
      {
        "id": "7430f8c0-bec9-417d-8d17-6d1073a3d4fa",
        "sort_order": 1,
        "is_active": true,
        "name": "Giáo sư",
        "abbreviation": "GS",
        "translations": {
          "vi": {
            "name": "Giáo sư",
            "abbreviation": "GS"
          },
          "en": {
            "name": "Professor",
            "abbreviation": "Prof."
          }
        }
      }
    ]
    ```

#### B. Danh sách Học vị
*   **Method / URL**: `GET /api/v1/admin/degrees`
*   **Response Body (200 OK)**:
    ```json
    [
      {
        "id": "c17f1648-ebc9-460e-96a0-026f94e082b5",
        "sort_order": 2,
        "is_active": true,
        "name": "Tiến sĩ",
        "abbreviation": "TS",
        "translations": {
          "vi": {
            "name": "Tiến sĩ",
            "abbreviation": "TS"
          },
          "en": {
            "name": "Doctor of Philosophy",
            "abbreviation": "Ph.D."
          }
        }
      }
    ]
    ```

---

## 2. PORTAL API (Trang chủ Website)

Tất cả các endpoint trong phân hệ Portal đều công khai và không yêu cầu Token.

> [!NOTE]
> Ngôn ngữ trả về được xác định theo thứ tự ưu tiên:
> 1. Query parameter `lang=en` hoặc `lang=vi`.
> 2. Header `Accept-Language` (ví dụ: `Accept-Language: en-US,en;q=0.9`).
> 3. Mặc định là Tiếng Việt (`vi`).

### 2.1 Lấy danh sách Giảng viên hoạt động (Đã dịch và làm phẳng)
*   **Method / URL**: `GET /api/v1/portal/staffs`
*   **Query Parameters**:
    *   `lang` (string, optional): Mã ngôn ngữ (`vi`/`en`).
    *   `department_id` (string, optional): Lọc theo bộ môn.
    *   `position_id` (string, optional): Lọc theo chức vụ.
*   **Response Body (200 OK - `lang=en`)**:
    ```json
    [
      {
        "id": "ad41c6bc-3e82-4750-83a5-002877a572ce",
        "department_id": "4ecf0178-26d8-4a48-9fef-1fc8daad0734",
        "position_id": "b45c5783-568a-4aa9-812c-653aa3dc2a95",
        "academic_title_id": "7430f8c0-bec9-417d-8d17-6d1073a3d4fa",
        "degree_id": "c17f1648-ebc9-460e-96a0-026f94e082b5",
        "full_name": "Nguyễn Văn A",
        "english_name": "A Nguyen Van",
        "slug": "nguyen-van-a",
        "avatar_object_key": "avatars/a.png",
        "email": "anv@university.edu.vn",
        "phone": "0987654321",
        "website": "anv.blog",
        "office": "Room 501, Building B1",
        "sort_order": 5,
        "academic_title": "Associate Professor",
        "degree": "Ph.D",
        "biography": "Long working history...",
        "research_interests": "Artificial Intelligence, Big Data",
        "department": {
          "id": "4ecf0178-26d8-4a48-9fef-1fc8daad0734",
          "thumbnail_object_key": "fit-thumb.png",
          "phone": "024-123456",
          "email": "fit@university.edu.vn",
          "website": "fit.university.edu.vn",
          "office": "Room 302",
          "sort_order": 10,
          "name": "Information Technology",
          "description": "Leading IT department"
        },
        "position": {
          "id": "b45c5783-568a-4aa9-812c-653aa3dc2a95",
          "sort_order": 5,
          "name": "Head of Department",
          "description": "Responsible for academic management"
        }
      }
    ]
    ```

### 2.2 Chi tiết Giảng viên theo Slug (Đã dịch và làm phẳng)
*   **Method / URL**: `GET /api/v1/portal/staffs/{slug}`
*   **Query Parameters**:
    *   `lang` (string, optional): Mã ngôn ngữ (`vi`/`en`).
*   **Response Body (200 OK - `lang=vi`)**:
    ```json
    {
      "id": "ad41c6bc-3e82-4750-83a5-002877a572ce",
      "department_id": "4ecf0178-26d8-4a48-9fef-1fc8daad0734",
      "position_id": "b45c5783-568a-4aa9-812c-653aa3dc2a95",
      "academic_title_id": "7430f8c0-bec9-417d-8d17-6d1073a3d4fa",
      "degree_id": "c17f1648-ebc9-460e-96a0-026f94e082b5",
      "full_name": "Nguyễn Văn A",
      "english_name": "A Nguyen Van",
      "slug": "nguyen-van-a",
      "avatar_object_key": "avatars/a.png",
      "email": "anv@university.edu.vn",
      "phone": "0987654321",
      "website": "anv.blog",
      "office": "Room 501, Building B1",
      "sort_order": 5,
      "academic_title": "Phó giáo sư",
      "degree": "Tiến sĩ",
      "biography": "Quá trình công tác dài hạn...",
      "research_interests": "Trí tuệ nhân tạo, Big Data",
      "department": {
        "id": "4ecf0178-26d8-4a48-9fef-1fc8daad0734",
        "thumbnail_object_key": "fit-thumb.png",
        "phone": "024-123456",
        "email": "fit@university.edu.vn",
        "website": "fit.university.edu.vn",
        "office": "Room 302",
        "sort_order": 10,
        "name": "Công nghệ thông tin",
        "description": "Khoa đào tạo CNTT hàng đầu"
      },
      "position": {
        "id": "b45c5783-568a-4aa9-812c-653aa3dc2a95",
        "sort_order": 5,
        "name": "Trưởng bộ môn",
        "description": "Quản lý chuyên môn của khoa"
      }
    }
    ```

### 2.3 Lấy danh sách Học hàm & Học vị cho Portal Website (Dành cho bộ lọc tìm kiếm)
Các endpoint công khai phục vụ bộ lọc tìm kiếm giảng viên ở Portal:

#### A. Danh sách Học hàm
*   **Method / URL**: `GET /api/v1/portal/academic-titles`
*   **Query Parameters**:
    *   `lang` (string, optional): Mã ngôn ngữ (`vi`/`en`).
*   **Response Body (200 OK - `lang=en`)**:
    ```json
    [
      {
        "id": "7430f8c0-bec9-417d-8d17-6d1073a3d4fa",
        "name": "Professor",
        "abbreviation": "Prof.",
        "sort_order": 1
      }
    ]
    ```

#### B. Danh sách Học vị
*   **Method / URL**: `GET /api/v1/portal/degrees`
*   **Query Parameters**:
    *   `lang` (string, optional): Mã ngôn ngữ (`vi`/`en`).
*   **Response Body (200 OK - `lang=vi`)**:
    ```json
    [
      {
        "id": "c17f1648-ebc9-460e-96a0-026f94e082b5",
        "name": "Tiến sĩ",
        "abbreviation": "TS",
        "sort_order": 2
      }
    ]
    ```

