# API Hồ sơ Cá nhân (Admin Profile Management)

> **Base URL:** `http://localhost:8000/api/v1/admin/profile`
> **Auth:** Tất cả endpoint đều yêu cầu Bearer Token trong header `Authorization`.
> Tất cả endpoint chỉ thao tác trên tài khoản của user đang đăng nhập — không có `user_id` param.

---

## TypeScript Interfaces

```typescript
// Response cho GET / và PUT /
interface MyProfileResponse {
  id: string;
  username: string;
  email: string;
  phone: string | null;
  full_name: string;
  bio: string | null;
  title: string | null;
  avatar_url: string | null;   // object_key từ MinIO, cần dùng getMediaUrl() để resolve
  roles: string[];             // ["super_admin"] hoặc ["admin"]
  is_active: boolean;
  last_login: string | null;   // ISO datetime
  created_at: string;          // ISO datetime
  updated_at: string;          // ISO datetime
}

// Request body cho PUT /
interface ProfileUpdateRequest {
  full_name?: string;          // min 1, max 100 ký tự
  phone?: string;              // max 20 ký tự
  bio?: string;                // không giới hạn
  title?: string;              // max 100 ký tự
  avatar_id?: string;          // UUID của media item
}

// Request body cho PUT /password
interface ChangePasswordRequest {
  current_password: string;    // bắt buộc
  new_password: string;        // min 6, max 100 ký tự
}

// Response item cho GET /sessions
interface SessionItem {
  id: string;
  ip_address: string;
  user_agent: string | null;
  created_at: string;
  expires_at: string;
  is_revoked: boolean;
}

// Response cho GET /login-history
interface LoginHistoryResponse {
  items: LoginHistoryItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

interface LoginHistoryItem {
  id: string;
  ip_address: string;
  user_agent: string | null;
  status: "success" | "failed";
  failure_reason: string | null;
  created_at: string;
}

// Response cho GET /activity
interface ActivityResponse {
  items: ActivityItem[];
  total: number;
}

interface ActivityItem {
  id: string;
  actor_id: string;
  actor_username: string;
  action: string;              // VD: "AUTH_LOGIN", "PASSWORD_CHANGED", "PROFILE_UPDATED", ...
  target_type: string;         // VD: "session", "user", "article", ...
  target_id: string | null;
  changes: Record<string, any> | null;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
}
```

---

## 1. Lấy hồ sơ chi tiết

```
GET /api/v1/admin/profile
```

**Response 200:**
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "username": "superadmin",
  "email": "admin@ktcn.edu.vn",
  "phone": null,
  "full_name": "System Super Administrator",
  "bio": null,
  "title": null,
  "avatar_url": "files/5539da7e93324cd5bf0af0caec5fe4f2",
  "roles": ["super_admin"],
  "is_active": true,
  "last_login": "2026-07-03T12:00:15.499945Z",
  "created_at": "2026-06-15T10:30:00Z",
  "updated_at": "2026-07-03T11:57:36Z"
}
```

> **Lưu ý `avatar_url`:** Trả về `object_key` từ MinIO (VD: `"files/5539da7e..."`) — FE cần dùng `getMediaUrl(avatar_url)` để tạo URL đầy đủ. Nếu user chưa có avatar thì trả `null`.

---

## 2. Cập nhật hồ sơ

```
PUT /api/v1/admin/profile
Content-Type: application/json
```

**Request body** (chỉ gửi field muốn thay đổi):
```json
{
  "full_name": "Nguyễn Văn A",
  "phone": "0901234567",
  "bio": "Quản trị viên hệ thống KTCN",
  "title": "Trưởng phòng CNTT",
  "avatar_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**Response 200:** Trả về `MyProfileResponse` đã cập nhật (cùng format như GET ở trên).

**Lỗi có thể gặp:**
- `422` — Validation lỗi (full_name quá dài, v.v.)

> **Quan trọng:** API này KHÔNG cho phép đổi `username`, `email`, `is_active`. Chỉ cho phép sửa 5 trường trên.

---

## 3. Đổi mật khẩu

```
PUT /api/v1/admin/profile/password
Content-Type: application/json
```

**Request body:**
```json
{
  "current_password": "Password@123",
  "new_password": "NewPassword@456"
}
```

**Response 200:**
```json
{
  "success": true,
  "message": "Đổi mật khẩu thành công"
}
```

**Lỗi có thể gặp:**
- `400` — `"Mật khẩu hiện tại không chính xác"` 
- `400` — `"Mật khẩu mới không được trùng với mật khẩu hiện tại"`
- `422` — Validation lỗi (new_password < 6 ký tự)

> **Lưu ý:** Sau khi đổi mật khẩu thành công, FE nên thông báo thành công. Access token hiện tại vẫn hoạt động bình thường cho tới khi hết hạn — KHÔNG cần logout.

---

## 4. Phiên đăng nhập

```
GET /api/v1/admin/profile/sessions
```

**Response 200:**
```json
[
  {
    "id": "d8f5a1b2-c3d4-e5f6-7890-abcdef123456",
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...",
    "created_at": "2026-07-03T08:30:00Z",
    "expires_at": "2026-07-11T08:30:00Z",
    "is_revoked": false
  },
  {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "ip_address": "10.0.0.50",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
    "created_at": "2026-07-02T15:00:00Z",
    "expires_at": "2026-07-10T15:00:00Z",
    "is_revoked": true
  }
]
```

> **Gợi ý UI:** Hiển thị danh sách card, mỗi card có IP, trình duyệt (parse từ user_agent), thời gian tạo, trạng thái (active/revoked). Có thể thêm nút "Thu hồi" gọi `POST /api/v1/auth/devices/{id}/revoke` (API này đã có sẵn từ trước).

---

## 5. Lịch sử đăng nhập

```
GET /api/v1/admin/profile/login-history?page=1&page_size=20&status=success
```

**Query params:**
| Param | Type | Default | Mô tả |
|-------|------|---------|--------|
| `page` | int | 1 | Trang hiện tại (1-based) |
| `page_size` | int | 20 | Số item mỗi trang |
| `status` | string | (tất cả) | Lọc theo: `"success"` hoặc `"failed"` |

**Response 200:**
```json
{
  "items": [
    {
      "id": "90d33de7-3448-4098-b4cf-39589774acea",
      "ip_address": "127.0.0.1",
      "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...",
      "status": "success",
      "failure_reason": null,
      "created_at": "2026-07-03T12:00:15Z"
    },
    {
      "id": "e85d82f9-1ae9-4b4a-bed5-816831598129",
      "ip_address": "192.168.1.50",
      "user_agent": "Mozilla/5.0 (Windows NT 10.0)...",
      "status": "failed",
      "failure_reason": "Sai mật khẩu",
      "created_at": "2026-07-03T11:55:00Z"
    }
  ],
  "total": 49,
  "page": 1,
  "page_size": 20,
  "total_pages": 3
}
```

> **Gợi ý UI:** Bảng có phân trang, cột trạng thái hiển thị badge xanh/đỏ cho success/failed. Nếu `failure_reason` không null thì hiển thị tooltip.

---

## 6. Nhật ký hoạt động

```
GET /api/v1/admin/profile/activity?limit=10
```

**Query params:**
| Param | Type | Default | Mô tả |
|-------|------|---------|--------|
| `limit` | int | 10 | Số hoạt động gần nhất (tối đa 50) |

**Response 200:**
```json
{
  "items": [
    {
      "id": "9f3806b5-a123-4780-b2e5-a854f3d1f01b",
      "actor_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "actor_username": "superadmin",
      "action": "AUTH_LOGIN",
      "target_type": "session",
      "target_id": null,
      "changes": { "ip": "127.0.0.1" },
      "ip_address": "127.0.0.1",
      "user_agent": "Mozilla/5.0...",
      "created_at": "2026-07-03T12:00:15Z"
    },
    {
      "id": "900bba64-075a-4fd4-aa0e-145d29e68c64",
      "actor_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "actor_username": "superadmin",
      "action": "PASSWORD_CHANGED",
      "target_type": "user",
      "target_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "changes": null,
      "ip_address": "127.0.0.1",
      "user_agent": "Mozilla/5.0...",
      "created_at": "2026-07-03T11:57:36Z"
    }
  ],
  "total": 355
}
```

**Tất cả các loại `action` trong hệ thống:**

| Nhóm | Action | Mô tả |
|------|--------|--------|
| Auth | `AUTH_LOGIN` | Đăng nhập |
| Auth | `AUTH_LOGOUT` | Đăng xuất |
| Auth | `AUTH_LOGOUT_ALL` | Đăng xuất tất cả thiết bị |
| Auth | `PASSWORD_CHANGED` | Đổi mật khẩu |
| Auth | `PROFILE_UPDATED` | Cập nhật hồ sơ |
| Auth | `DEVICE_REVOKED` | Thu hồi phiên đăng nhập |
| User | `USER_CREATED` | Tạo thành viên |
| User | `USER_UPDATED` | Sửa thành viên |
| User | `USER_DELETED` | Xóa thành viên |
| User | `USER_LOCKED` | Khóa tài khoản |
| User | `USER_UNLOCKED` | Mở khóa tài khoản |
| User | `ROLE_UPDATED` | Sửa vai trò |
| User | `ROLE_PERMISSIONS_CHANGED` | Đổi quyền vai trò |
| Article | `ARTICLE_CREATED` | Tạo bài viết |
| Article | `ARTICLE_UPDATED` | Sửa bài viết |
| Article | `ARTICLE_DELETED` | Xóa bài viết |
| Article | `ARTICLE_PUBLISHED` | Đăng bài viết |
| Article | `ARTICLE_AUTO_PUBLISHED` | Tự động đăng bài |
| Article | `ARTICLE_ARCHIVED` | Lưu trữ bài viết |
| Article | `ARTICLE_RESTORED` | Khôi phục bài viết |
| Category | `CATEGORY_CREATED` | Tạo danh mục |
| Category | `CATEGORY_UPDATED` | Sửa danh mục |
| Category | `CATEGORY_DELETED` | Xóa danh mục |
| Category | `CATEGORY_RESTORED` | Khôi phục danh mục |
| Category | `CATEGORIES_REORDERED` | Sắp xếp danh mục |
| Tag | `TAG_CREATED` | Tạo thẻ |
| Tag | `TAG_UPDATED` | Sửa thẻ |
| Tag | `TAG_DELETED` | Xóa thẻ |
| Tag | `TAG_STATUS_TOGGLED` | Đổi trạng thái thẻ |
| Menu | `MENU_CREATED` | Tạo menu |
| Menu | `MENU_ITEM_CREATED` | Tạo mục menu |
| Menu | `MENU_ITEM_UPDATED` | Sửa mục menu |
| Menu | `MENU_ITEM_DELETED` | Xóa mục menu |
| Menu | `MENU_ITEMS_REORDERED` | Sắp xếp menu |
| Dept | `DEPARTMENT_CREATED` | Tạo phòng ban |
| Dept | `DEPARTMENT_UPDATED` | Sửa phòng ban |
| Dept | `DEPARTMENT_DELETED` | Xóa phòng ban |
| Dept | `DEPARTMENT_STATUS_UPDATED` | Đổi TT phòng ban |
| Position | `POSITION_CREATED` | Tạo chức vụ |
| Position | `POSITION_UPDATED` | Sửa chức vụ |
| Position | `POSITION_DELETED` | Xóa chức vụ |
| Position | `POSITION_STATUS_UPDATED` | Đổi TT chức vụ |
| Staff | `STAFF_CREATED` | Tạo nhân sự |
| Staff | `STAFF_UPDATED` | Sửa nhân sự |
| Staff | `STAFF_DELETED` | Xóa nhân sự |
| Staff | `STAFF_STATUS_UPDATED` | Đổi TT nhân sự |
| Language | `LANGUAGE_CREATED` | Tạo ngôn ngữ |
| Language | `LANGUAGE_UPDATED` | Sửa ngôn ngữ |
| Language | `LANGUAGE_DELETED` | Xóa ngôn ngữ |
| Language | `LANGUAGE_ENABLED` | Bật ngôn ngữ |
| Language | `LANGUAGE_DISABLED` | Tắt ngôn ngữ |
| Language | `LANGUAGE_SET_DEFAULT` | Đặt NN mặc định |
| Language | `LANGUAGE_RESTORED` | Khôi phục ngôn ngữ |
| Language | `LANGUAGES_REORDERED` | Sắp xếp ngôn ngữ |
| Banner | `BANNER_CREATED` | Tạo banner |
| Banner | `BANNER_UPDATED` | Sửa banner |
| Banner | `BANNER_DELETED` | Xóa banner |
| Media | `MEDIA_UPLOADED` | Tải lên media |
| AI | `AI_SETTINGS_UPDATED` | Cập nhật cài đặt AI |

---

## Gợi ý cấu trúc trang Profile

Trang `/profile` nên chia thành các tab hoặc section:

1. **Thông tin cá nhân** — Form sửa: full_name, phone, bio, title, upload avatar → gọi `PUT /admin/profile`
2. **Bảo mật** — Form đổi mật khẩu → gọi `PUT /admin/profile/password`
3. **Phiên đăng nhập** — Danh sách session + nút thu hồi → gọi `GET /admin/profile/sessions`
4. **Lịch sử đăng nhập** — Bảng có phân trang + filter status → gọi `GET /admin/profile/login-history`
5. **Nhật ký hoạt động** — Timeline các hành động gần đây → gọi `GET /admin/profile/activity`

---

## Xử lý lỗi chung

Tất cả API đều có thể trả:
- `401` — Token hết hạn hoặc không hợp lệ → redirect về login
- `403` — Tài khoản bị khóa
- `422` — Validation error (request body sai format)
- `400` — Business logic error (mật khẩu sai, v.v.) — xem field `message` trong response
