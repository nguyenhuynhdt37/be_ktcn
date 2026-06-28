# API Documentation — Production Hardening Updates

> **Phiên bản**: 1.2.0  
> **Ngày cập nhật**: 2026-06-27  
> **Base URL**: `/api/v1`

---

## Mục lục

1. [Rate Limiting (Chống brute-force)](#1-rate-limiting)
2. [Check Username API](#2-check-username-api)
3. [Soft Delete User](#3-soft-delete-user)
4. [Audit Log API](#4-audit-log-api)
5. [Tổng hợp Audit Actions](#5-tổng-hợp-audit-actions)

---

## 1. Rate Limiting

### Cơ chế

- Áp dụng cho: `POST /api/v1/auth/login`
- Giới hạn: **5 lần đăng nhập thất bại / phút / IP**
- Khi vượt giới hạn → trả về HTTP **429 Too Many Requests**
- Counter tự động reset khi đăng nhập thành công

### Response khi bị chặn

```json
{
  "success": false,
  "error": {
    "code": "TOO_MANY_REQUESTS",
    "message": "Quá nhiều lần đăng nhập thất bại. Vui lòng thử lại sau 45 giây.",
    "details": {
      "retry_after": 45
    }
  }
}
```

| Field | Type | Mô tả |
|---|---|---|
| `retry_after` | `number` | Số giây cần chờ trước khi thử lại |

### Gợi ý FE

- Khi nhận `429`, hiển thị thông báo với countdown timer từ `retry_after`
- Disable nút "Đăng nhập" trong khoảng thời gian chờ

---

## 2. Check Username API

### `GET /api/v1/users/check-username`

Kiểm tra xem username đã tồn tại trong hệ thống hay chưa.  
Tương tự API `check-email` đã có.

**Yêu cầu**: Đăng nhập (Bearer Token)

#### Query Parameters

| Param | Type | Required | Mô tả |
|---|---|---|---|
| `username` | `string` | ✅ | Username cần kiểm tra |

#### Response `200 OK`

```json
{
  "exists": true
}
```

```json
{
  "exists": false
}
```

### Gợi ý FE

- Dùng `debounce` (300-500ms) khi user gõ username để gọi API kiểm tra real-time
- Hiển thị icon ✅/❌ bên cạnh input field
- Kết hợp với `check-email` để validate cả 2 trường trước khi submit form

---

## 3. Soft Delete User

### Thay đổi hành vi

- `DELETE /api/v1/users/{user_id}` giờ thực hiện **soft delete** thay vì hard delete
- User bị xóa mềm sẽ:
  - ❌ Không xuất hiện trong danh sách users (`GET /api/v1/users`)
  - ❌ Không thể đăng nhập
  - ❌ Không thể xem chi tiết (`GET /api/v1/users/{user_id}` → 404)
  - ✅ Dữ liệu vẫn tồn tại trong DB (có thể khôi phục bởi admin DB)

### Response không thay đổi

```json
{
  "success": true
}
```

### Gợi ý FE

- Có thể hiển thị thông báo: "Tài khoản đã được xóa mềm. Liên hệ quản trị viên nếu cần khôi phục."
- UX không đổi so với trước — API request/response giữ nguyên

---

## 4. Audit Log API

### `GET /api/v1/audit-logs`

Lấy danh sách nhật ký hành động quản trị phân trang.

**Yêu cầu quyền**: `audit.view` hoặc Super Admin

#### Query Parameters

| Param | Type | Required | Default | Mô tả |
|---|---|---|---|---|
| `page` | `integer` | ❌ | `1` | Trang hiện tại |
| `page_size` | `integer` | ❌ | `20` | Số bản ghi / trang |
| `action` | `string` | ❌ | — | Lọc theo loại hành động (xem bảng bên dưới) |
| `target_type` | `string` | ❌ | — | Lọc theo loại đối tượng: `user`, `role`, `session`, `media` |
| `actor_id` | `uuid` | ❌ | — | Lọc theo người thực hiện |
| `from_date` | `datetime` | ❌ | — | Lọc từ ngày (ISO 8601) |
| `to_date` | `datetime` | ❌ | — | Lọc đến ngày (ISO 8601) |

#### Response `200 OK`

```json
{
  "items": [
    {
      "id": "a1b2c3d4-...",
      "actor_id": "3fa85f64-...",
      "actor_username": "admin",
      "action": "USER_CREATED",
      "target_type": "user",
      "target_id": "5fa85f64-...",
      "changes": {
        "username": "newuser",
        "email": "newuser@example.com",
        "roles": ["editor"]
      },
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0 ...",
      "created_at": "2026-06-27T18:30:00Z"
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8
}
```

#### Audit Log Item Schema

| Field | Type | Nullable | Mô tả |
|---|---|---|---|
| `id` | `uuid` | ❌ | ID của bản ghi log |
| `actor_id` | `uuid` | ✅ | ID người thực hiện hành động |
| `actor_username` | `string` | ❌ | Username người thực hiện |
| `action` | `string` | ❌ | Loại hành động (xem bảng bên dưới) |
| `target_type` | `string` | ❌ | Loại đối tượng bị tác động |
| `target_id` | `uuid` | ✅ | ID đối tượng bị tác động |
| `changes` | `object` | ✅ | JSON chứa chi tiết thay đổi (diff) |
| `ip_address` | `string` | ✅ | Địa chỉ IP của người thực hiện |
| `user_agent` | `string` | ✅ | Trình duyệt / Client info |
| `created_at` | `datetime` | ❌ | Thời điểm ghi log |

---

## 5. Tổng hợp Audit Actions

Hệ thống ghi lại **tất cả hành động thay đổi dữ liệu** trên mọi module:

### Auth & Session

| Action | Target Type | Mô tả | Changes |
|---|---|---|---|
| `AUTH_LOGIN` | `session` | Đăng nhập thành công | `{"ip": "..."}` |
| `AUTH_LOGOUT` | `session` | Đăng xuất | — |
| `AUTH_LOGOUT_ALL` | `session` | Đăng xuất tất cả thiết bị | — |
| `DEVICE_REVOKED` | `session` | Thu hồi phiên đăng nhập cụ thể | — |

### User Management

| Action | Target Type | Mô tả | Changes |
|---|---|---|---|
| `USER_CREATED` | `user` | Tạo người dùng mới | `{"username", "email", "roles"}` |
| `USER_UPDATED` | `user` | Cập nhật thông tin người dùng | `{fields changed}` |
| `USER_DELETED` | `user` | Xóa mềm người dùng | — |
| `USER_LOCKED` | `user` | Khóa tài khoản | — |
| `USER_UNLOCKED` | `user` | Mở khóa tài khoản | — |

### Role Management

| Action | Target Type | Mô tả | Changes |
|---|---|---|---|
| `ROLE_CREATED` | `role` | Tạo vai trò mới | `{"name", "code"}` |
| `ROLE_UPDATED` | `role` | Cập nhật vai trò | `{fields changed}` |
| `ROLE_DELETED` | `role` | Xóa vai trò | — |
| `ROLE_PERMISSIONS_CHANGED` | `role` | Thay đổi quyền của vai trò | `{"permission_ids": [...]}` |

### Media Management

| Action | Target Type | Mô tả | Changes |
|---|---|---|---|
| `MEDIA_FOLDER_CREATED` | `media` | Tạo thư mục mới | `{"name", "parent_id"}` |
| `MEDIA_UPLOADED` | `media` | Upload file | `{"filename", "content_type", "size"}` |
| `MEDIA_RENAMED` | `media` | Đổi tên | `{"new_name"}` |
| `MEDIA_MOVED` | `media` | Di chuyển | `{"new_parent_id"}` |
| `MEDIA_COPIED` | `media` | Sao chép | `{"dest_parent_id"}` |
| `MEDIA_DELETED` | `media` | Xóa file/thư mục | — |

---

## Gợi ý triển khai FE cho Audit Log

### Trang Audit Log (dành cho Super Admin)

1. **Bảng danh sách** phân trang, hiển thị: thời gian, người thực hiện, hành động, đối tượng
2. **Bộ lọc**:
   - Dropdown: Action type (USER_CREATED, ROLE_DELETED, ...)
   - Dropdown: Target type (user, role, session, media)
   - Date range picker: from_date → to_date
   - Search by actor
3. **Chi tiết**: Click vào row → hiển thị modal/drawer chứa JSON `changes`
4. **Color coding**:
   - 🟢 `CREATED` → xanh lá
   - 🟡 `UPDATED` → vàng
   - 🔴 `DELETED` → đỏ
   - 🔵 `LOGIN/LOGOUT` → xanh dương

---

## Database Indexes đã bổ sung

Các index sau đã được thêm để tối ưu hiệu suất query:

| Index | Table | Column(s) | Mục đích |
|---|---|---|---|
| `idx_users_is_active` | `users` | `is_active` | Filter user theo trạng thái |
| `idx_users_created_at` | `users` | `created_at DESC` | Sort user theo ngày tạo |
| `idx_users_deleted_at` | `users` | `deleted_at` | Filter soft delete |
| `idx_login_histories_user_id` | `login_histories` | `user_id` | Lookup lịch sử login |
| `idx_login_histories_created_at` | `login_histories` | `created_at DESC` | Sort lịch sử |
| `idx_refresh_tokens_user_id` | `refresh_tokens` | `user_id` | Lookup session |
| `idx_refresh_tokens_expires_at` | `refresh_tokens` | `expires_at` | Cleanup expired |
| `idx_media_items_parent_id` | `media_items` | `parent_id` | Tree traversal |
| `idx_audit_logs_actor_id` | `audit_logs` | `actor_id` | Filter by actor |
| `idx_audit_logs_action` | `audit_logs` | `action` | Filter by action |
| `idx_audit_logs_target_type` | `audit_logs` | `target_type` | Filter by type |
| `idx_audit_logs_created_at` | `audit_logs` | `created_at DESC` | Sort by time |
