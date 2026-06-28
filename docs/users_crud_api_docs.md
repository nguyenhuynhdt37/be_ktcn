# Users CRUD and Profiles Management API

> Hướng dẫn tích hợp hệ thống quản lý Thành viên (Users CRUD), kiểm tra email trùng và Hồ sơ cá nhân chuẩn Production dành cho **Frontend Developer**.
> Base URL: `http://localhost:8000/api/v1`
> Header xác thực: `Authorization: Bearer <access_token>`

---

## 1. Phân quyền & Quy định bảo mật (RBAC & Guard Rules)

### Bảng phân quyền gọi API:
| API Endpoints | Hành động | Quyền yêu cầu |
|---|---|---|
| `GET /users` | Lấy danh sách thành viên phân trang/lọc | `user.view` |
| `GET /users/check-email` | Kiểm tra trùng email (phục vụ validation) | Đăng nhập |
| `GET /users/{id}` | Lấy thông tin chi tiết của thành viên | `user.view` |
| `POST /users` | Thêm mới thành viên | `user.create` |
| `PUT /users/{id}` | Cập nhật thông tin/vai trò thành viên | `user.update` |
| `DELETE /users/{id}` | Xóa thành viên | `user.delete` |

### Quy tắc bảo vệ đặc biệt (Production-grade Guards):
1. **Chặn leo thang quyền lực (Privilege Escalation Protection)**:
   - Khi `POST /users` hoặc `PUT /users/{id}`, người vận hành có thể chỉ định danh sách `role_ids` cho thành viên.
   - **Quy tắc**: Chỉ tài khoản có vai trò `super_admin` mới có quyền gán hoặc gỡ vai trò `super_admin` cho người khác. Nếu một Admin thường cố gán vai trò `super_admin`, hệ thống sẽ trả về lỗi `SUPERADMIN_ASSIGNMENT_DENIED` (HTTP 400).
2. **Bảo vệ Super Admin**:
   - Không cho phép cập nhật trạng thái hoạt động (`is_active`) hoặc vai trò của tài khoản `super_admin` bởi bất kỳ ai ngoại trừ chính Super Admin. Trả về `SUPERADMIN_ROLE_PROTECTED` (HTTP 400).
   - Không cho phép xóa tài khoản Super Admin. Trả về `SUPERADMIN_DELETION_DENIED` (HTTP 400).
3. **Chặn tự xóa chính mình**:
   - Thành viên không thể tự gọi API xóa chính mình. Trả về `SELF_DELETION_DENIED` (HTTP 400).

---

## 2. Đặc tả API Chi tiết

### 2.1. Kiểm tra trùng Email (Validation API)
API dùng để kiểm tra xem một email đã tồn tại trong hệ thống hay chưa, phục vụ cho validation trực tiếp (real-time validation) khi người dùng đang nhập trên form.
- **Request**:
  - `GET /api/v1/users/check-email?email=test@university.edu.vn`
- **Response `200 OK`**:
  ```json
  {
    "exists": true // true nếu email đã bị trùng, false nếu email hợp lệ/chưa sử dụng
  }
  ```

---

### 2.2. Thêm mới thành viên
- **Request**:
  - `POST /api/v1/users`
  - `Content-Type: application/json`
  - Body:
    ```json
    {
      "username": "hoang_editor",
      "email": "hoang.editor@university.edu.vn",
      "password": "Password123!",
      "full_name": "Nguyễn Minh Hoàng",
      "phone": "0912345678",
      "bio": "Biên tập viên thuộc Ban Truyền thông của trường Đại học",
      "title": "Chuyên viên truyền thông",
      "avatar_id": "d80ef748-0c31-416b-a25e-bf332cfa8a29", // Cần upload ảnh lên module Media trước để lấy avatar_id
      "role_ids": ["d1017cf7-88b3-4f9e-c616-3e4b3c75ad03"],
      "is_active": true
    }
    ```
- **Response `200 OK`**:
  ```json
  {
    "id": "e98ff541-b849-5f21-9988-c0a76a5bfe20",
    "username": "hoang_editor",
    "email": "hoang.editor@university.edu.vn",
    "phone": "0912345678",
    "full_name": "Nguyễn Minh Hoàng",
    "bio": "Biên tập viên thuộc Ban Truyền thông của trường Đại học",
    "title": "Chuyên viên truyền thông",
    "avatar_id": "d80ef748-0c31-416b-a25e-bf332cfa8a29",
    "avatar": {
      "id": "d80ef748-0c31-416b-a25e-bf332cfa8a29",
      "name": "avatar.png",
      "is_folder": false,
      "parent_id": null,
      "object_key": "files/avatar_key",
      "thumbnail_key": "thumbs/avatar_key_thumb",
      "bucket": "university-media",
      "mime_type": "image/png",
      "size": 15420,
      "checksum": "d41d8cd98f00b204e9800998ecf8427e",
      "width": 500,
      "height": 500,
      "created_at": "2026-06-27T08:00:00Z",
      "updated_at": "2026-06-27T08:00:00Z"
    },
    "is_active": true,
    "created_at": "2026-06-27T15:20:00Z",
    "updated_at": "2026-06-27T15:20:00Z",
    "roles": [
      {
        "id": "d1017cf7-88b3-4f9e-c616-3e4b3c75ad03",
        "name": "Editor Role",
        "code": "editor"
      }
    ]
  }
  ```

---

### 2.3. Lấy thông tin chi tiết thành viên
- **Request**:
  - `GET /api/v1/users/e98ff541-b849-5f21-9988-c0a76a5bfe20`
- **Response `200 OK`**:
  *(Trả về object đầy đủ tương tự định dạng của API tạo mới ở trên)*

---

### 2.4. Cập nhật thông tin thành viên
- **Request**:
  - `PUT /api/v1/users/e98ff541-b849-5f21-9988-c0a76a5bfe20`
  - Body (gửi các trường cần sửa, các trường khác để null hoặc bỏ qua):
    ```json
    {
      "full_name": "Nguyễn Minh Hoàng (Ban Truyền thông)",
      "bio": "Mô tả mới được cập nhật",
      "role_ids": ["d1017cf7-88b3-4f9e-c616-3e4b3c75ad03"]
    }
    ```
- **Response `200 OK`**:
  *(Trả về object chi tiết sau khi cập nhật)*

---

### 2.5. Xóa thành viên
- **Request**:
  - `DELETE /api/v1/users/e98ff541-b849-5f21-9988-c0a76a5bfe20`
- **Response `200 OK`**:
  ```json
  {
    "success": true
  }
  ```

---

## 3. Danh sách Mã lỗi & Xử lý (Error Codes)

| HTTP Status | error_code | Ý nghĩa & Cách xử lý |
|---|---|---|
| `400` | `SUPERADMIN_ASSIGNMENT_DENIED` | Không có quyền gán/gỡ vai trò Super Admin (chỉ Super Admin mới gán được vai trò này). |
| `400` | `SUPERADMIN_ROLE_PROTECTED` | Chặn sửa đổi thông tin/vai trò hoặc vô hiệu hóa tài khoản Super Admin. |
| `400` | `SUPERADMIN_DELETION_DENIED` | Chặn xóa tài khoản quản trị tối cao (Super Admin). |
| `400` | `SELF_DELETION_DENIED` | Chặn tự xóa chính tài khoản đang đăng nhập. |
| `400` | `AVATAR_NOT_FOUND` | Tệp ảnh `avatar_id` cung cấp không tồn tại trong module Media. |
| `400` | `INVALID_ROLES_ASSIGNED` | Danh sách ID vai trò gán chứa ID không tồn tại. |
| `409` | `USERNAME_DUPLICATE` | Tên đăng nhập đã tồn tại trên hệ thống. |
| `409` | `EMAIL_DUPLICATE` | Địa chỉ email đã được sử dụng bởi người dùng khác. |

---

## 4. Hướng dẫn tích hợp Frontend (TypeScript & React Query)

### 4.1. Interfaces mô tả kiểu dữ liệu

```typescript
export interface UserDetail {
  id: string;
  username: string;
  email: string;
  phone: string | null;
  full_name: string;
  bio: string | null;
  title: string | null;
  avatar_id: string | null;
  avatar: {
    id: string;
    name: string;
    object_key: string;
    thumbnail_key: string | null;
    mime_type: string;
    size: number;
  } | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  roles: Array<{ id: string; name: string; code: string }>;
}

export interface UserCreatePayload {
  username: string;
  email: string;
  password?: string;
  full_name: string;
  phone?: string;
  bio?: string;
  title?: string;
  avatar_id?: string;
  role_ids?: string[];
  is_active?: boolean;
}
```

### 4.2. Tích hợp Đẩy ảnh đại diện (Avatar Workflow)
Để cập nhật avatar, Frontend cần tuân thủ luồng sau:
1. **Upload ảnh**: Gọi API của module Media (`POST /api/v1/media/upload`) để tải tệp ảnh lên server.
2. **Lấy ID**: Nhận phản hồi từ module Media chứa `id` của file vừa tạo (ví dụ: `d80ef748-0c31-416b-a25e-bf332cfa8a29`).
3. **Gửi payload**: Đưa ID này vào trường `avatar_id` khi gọi API tạo mới/cập nhật thành viên (`POST /users` hoặc `PUT /users/{id}`).

---

## 5. Checklist UX chuẩn chỉ dành cho Frontend
* [ ] **Ẩn nút Xóa/Sửa**: Ẩn hoặc disable nút Xóa và các checkbox vai trò đối với tài khoản là `super_admin` (chỉ cho phép chính Super Admin chỉnh sửa).
* [ ] **Cảnh báo lỗi tự xóa**: Nếu phát sinh lỗi `SELF_DELETION_DENIED`, hiển thị thông báo thân thiện: "Bạn không thể tự xóa chính tài khoản của mình."
* [ ] **Kiểm tra trùng email tự động**: Thêm debounce 500ms khi người dùng nhập email và gọi API `GET /check-email?email=...` để hiển thị cảnh báo đỏ ngay nếu trùng.
* [ ] **Đồng bộ hóa avatar**: Sau khi upload ảnh thành công, cập nhật ngay lập tức giao diện xem trước (Preview) bằng thumbnail được trả về trước khi bấm "Lưu".
