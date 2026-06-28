# Account Activity Monitoring API

> Tài liệu này dành cho **Frontend Developer**.  
> Base URL: `http://localhost:8000/api/v1`  
> Tất cả endpoint đều yêu cầu header `Authorization: Bearer <access_token>`.

---

## Mục lục

1. [Xác thực & Quyền](#1-xác-thực--quyền)
2. [GET /users/{id}/sessions](#2-get-usersidsessions)
3. [GET /users/{id}/login-history](#3-get-usersidlogin-history)
4. [POST /users/{id}/sessions/{session_id}/revoke](#4-post-usersidsessionssession_idrevoke)
5. [POST /users/{id}/sessions/revoke-all](#5-post-usersidsessionsrevoke-all)
6. [POST /users/{id}/lock](#6-post-usersidlock)
7. [POST /users/{id}/unlock](#7-post-usersidunlock)
8. [GET /users/{id}/anomalies](#8-get-usersidanomalies)
9. [Cấu trúc lỗi chung](#9-cấu-trúc-lỗi-chung)
10. [Hướng dẫn tích hợp FE](#10-hướng-dẫn-tích-hợp-fe)

---

## 1. Xác thực & Quyền

### Cơ chế xác thực
Tất cả request đều phải gửi kèm JWT access token trong header:
```
Authorization: Bearer <access_token>
```

### ⚠️ Chỉ dành cho Super Admin

**Toàn bộ 7 endpoint trong tài liệu này chỉ cho phép tài khoản có role `super_admin` truy cập.**  
Mọi tài khoản khác, dù có các quyền `user.view`, `user.update`, v.v., đều bị từ chối với mã lỗi `SUPERADMIN_REQUIRED` (HTTP 403).

| Endpoint | Role yêu cầu |
|---|---|
| Tất cả 7 endpoint bên dưới | `super_admin` (bắt buộc) |

> **Lý do**: Các thao tác theo dõi hoạt động, khoá tài khoản và phát hiện bất thường thuộc nhóm chức năng quản trị cấp cao. Chỉ Super Admin mới có quyền kiểm soát trực tiếp phiên đăng nhập và trạng thái tài khoản của người dùng khác.

---

## 2. GET /users/{id}/sessions

Lấy danh sách tất cả phiên đăng nhập (còn hạn) của một tài khoản — bao gồm cả phiên đang hoạt động và đã bị thu hồi.

**Quyền yêu cầu:** `user.view`

### Request

```http
GET /api/v1/users/{user_id}/sessions
Authorization: Bearer <access_token>
```

| Tham số | Vị trí | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|---|
| `user_id` | path | UUID | ✅ | ID của người dùng cần xem |

### Response `200 OK`

```json
[
  {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "ip_address": "113.161.45.12",
    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "created_at": "2024-01-15T08:30:00Z",
    "expires_at": "2024-01-23T08:30:00Z",
    "is_revoked": false
  },
  {
    "id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "ip_address": "192.168.1.5",
    "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0)",
    "created_at": "2024-01-14T21:15:00Z",
    "expires_at": "2024-01-22T21:15:00Z",
    "is_revoked": true
  }
]
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `id` | UUID | ID duy nhất của phiên |
| `ip_address` | string | Địa chỉ IP đăng nhập |
| `user_agent` | string \| null | Trình duyệt / thiết bị |
| `created_at` | ISO 8601 datetime | Thời điểm tạo phiên |
| `expires_at` | ISO 8601 datetime | Thời điểm hết hạn |
| `is_revoked` | boolean | `true` = đã bị thu hồi |

### Response lỗi

| HTTP | error_code | Nguyên nhân |
|---|---|---|
| `401` | `UNAUTHORIZED` | Thiếu hoặc token hết hạn |
| `403` | `FORBIDDEN_ACCESS` | Không có quyền `user.view` |

---

## 3. GET /users/{id}/login-history

Lấy lịch sử đăng nhập có phân trang của một tài khoản. Bao gồm cả lần đăng nhập thành công và thất bại.

**Quyền yêu cầu:** `user.view`

### Request

```http
GET /api/v1/users/{user_id}/login-history?page=1&page_size=20&status=failed
Authorization: Bearer <access_token>
```

| Tham số | Vị trí | Kiểu | Mặc định | Mô tả |
|---|---|---|---|---|
| `user_id` | path | UUID | — | ID người dùng |
| `page` | query | integer | `1` | Số trang |
| `page_size` | query | integer | `20` | Số bản ghi mỗi trang (max 100) |
| `status` | query | string | — | Lọc theo trạng thái: `success` hoặc `failed` |

### Response `200 OK`

```json
{
  "items": [
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "ip_address": "113.161.45.12",
      "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
      "status": "success",
      "failure_reason": null,
      "created_at": "2024-01-15T08:30:00Z"
    },
    {
      "id": "1c7b7f94-9a2b-4e5d-8b3e-4d2c1f9a8b7c",
      "ip_address": "5.5.5.5",
      "user_agent": "python-requests/2.31.0",
      "status": "failed",
      "failure_reason": "incorrect_credentials",
      "created_at": "2024-01-15T03:22:10Z"
    }
  ],
  "total": 47,
  "page": 1,
  "page_size": 20,
  "total_pages": 3
}
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `items` | array | Danh sách bản ghi đăng nhập |
| `status` | `"success"` \| `"failed"` | Kết quả đăng nhập |
| `failure_reason` | string \| null | Lý do thất bại: `incorrect_credentials`, `inactive_user` |
| `total` | integer | Tổng số bản ghi |
| `total_pages` | integer | Tổng số trang |

---

## 4. POST /users/{id}/sessions/{session_id}/revoke

Thu hồi (đăng xuất từ xa) một phiên đăng nhập cụ thể của người dùng.

**Quyền yêu cầu:** `user.update`

### Request

```http
POST /api/v1/users/{user_id}/sessions/{session_id}/revoke
Authorization: Bearer <access_token>
```

| Tham số | Vị trí | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|---|
| `user_id` | path | UUID | ✅ | ID người dùng |
| `session_id` | path | UUID | ✅ | ID phiên cần thu hồi (lấy từ API sessions) |

> Không cần request body.

### Response `200 OK`

```json
{
  "success": true
}
```

### Response lỗi

| HTTP | error_code | Nguyên nhân |
|---|---|---|
| `404` | `SESSION_NOT_FOUND` | Phiên không tồn tại hoặc không thuộc user này |
| `403` | `FORBIDDEN_ACCESS` | Không có quyền `user.update` |

---

## 5. POST /users/{id}/sessions/revoke-all

Thu hồi tất cả phiên đăng nhập đang hoạt động của một người dùng. Người dùng đó sẽ bị đăng xuất trên tất cả thiết bị.

**Quyền yêu cầu:** `user.update`

### Request

```http
POST /api/v1/users/{user_id}/sessions/revoke-all
Authorization: Bearer <access_token>
```

> Không cần request body.

### Response `200 OK`

```json
{
  "success": true,
  "revoked_count": 3
}
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `success` | boolean | Luôn `true` nếu request thành công |
| `revoked_count` | integer | Số phiên đã bị thu hồi |

---

## 6. POST /users/{id}/lock

Khoá tài khoản người dùng. Sau khi khoá:
- Người dùng **không thể đăng nhập**
- Tất cả **phiên hiện tại bị thu hồi ngay lập tức**
- Access token hiện tại vẫn còn hạn nhưng mọi request tiếp theo của họ sẽ nhận `401`

**Quyền yêu cầu:** `user.lock`

### Request

```http
POST /api/v1/users/{user_id}/lock
Authorization: Bearer <access_token>
```

> Không cần request body.

### Response `200 OK`

```json
{
  "success": true,
  "message": "Tài khoản john_doe đã bị khoá và tất cả phiên đăng nhập đã bị thu hồi",
  "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "is_active": false
}
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `success` | boolean | `true` nếu thành công |
| `message` | string | Thông báo xác nhận bằng tiếng Việt |
| `user_id` | UUID | ID người dùng vừa bị khoá |
| `is_active` | boolean | Luôn `false` sau khi khoá |

### Response lỗi

| HTTP | error_code | Nguyên nhân |
|---|---|---|
| `404` | `USER_NOT_FOUND` | Người dùng không tồn tại |
| `403` | `FORBIDDEN_ACCESS` | Không có quyền `user.lock` |

---

## 7. POST /users/{id}/unlock

Mở khoá tài khoản người dùng, cho phép đăng nhập trở lại.

**Quyền yêu cầu:** `user.unlock`

### Request

```http
POST /api/v1/users/{user_id}/unlock
Authorization: Bearer <access_token>
```

> Không cần request body.

### Response `200 OK`

```json
{
  "success": true,
  "message": "Tài khoản john_doe đã được mở khoá thành công",
  "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "is_active": true
}
```

### Response lỗi

| HTTP | error_code | Nguyên nhân |
|---|---|---|
| `404` | `USER_NOT_FOUND` | Người dùng không tồn tại |
| `403` | `FORBIDDEN_ACCESS` | Không có quyền `user.unlock` |

---

## 8. GET /users/{id}/anomalies

Tạo báo cáo phân tích hành vi bất thường cho một tài khoản dựa trên lịch sử đăng nhập và trạng thái phiên hiện tại.

**Quyền yêu cầu:** `user.view`

### Luật phát hiện

| Loại | Điều kiện | Mức độ |
|---|---|---|
| `BRUTE_FORCE` | ≥5 lần thất bại trong bất kỳ cửa sổ 15 phút nào trong 24h qua | 🔴 CRITICAL |
| `NEW_LOCATION` | Đăng nhập thành công từ IP chưa từng xuất hiện trong 24h qua | 🟠 HIGH |
| `UNUSUAL_HOUR` | Đăng nhập ngoài khoảng 06:00–23:00 (giờ Việt Nam UTC+7) trong 24h qua | 🟡 MEDIUM |
| `MULTI_SESSION` | Có >5 phiên đang hoạt động đồng thời | 🔵 LOW |

### Request

```http
GET /api/v1/users/{user_id}/anomalies
Authorization: Bearer <access_token>
```

### Response `200 OK`

```json
{
  "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "risk_level": "HIGH",
  "anomalies": [
    {
      "type": "BRUTE_FORCE",
      "description": "Phát hiện 7 lần đăng nhập thất bại trong vòng 15 phút (bắt đầu từ 02:14 15/01/2024)",
      "severity": "CRITICAL",
      "detected_at": "2024-01-15T09:00:00Z"
    },
    {
      "type": "NEW_LOCATION",
      "description": "Đăng nhập thành công từ 2 địa chỉ IP mới chưa từng xuất hiện: 5.5.5.5, 8.8.8.8",
      "severity": "HIGH",
      "detected_at": "2024-01-15T09:00:00Z"
    }
  ],
  "active_session_count": 2,
  "failed_login_count_24h": 7,
  "generated_at": "2024-01-15T09:00:00Z"
}
```

| Trường | Kiểu | Mô tả |
|---|---|---|
| `risk_level` | string | Mức rủi ro tổng hợp: `SAFE` / `LOW` / `MEDIUM` / `HIGH` / `CRITICAL` |
| `anomalies` | array | Danh sách bất thường phát hiện được |
| `anomalies[].type` | string | Loại bất thường: `BRUTE_FORCE`, `NEW_LOCATION`, `UNUSUAL_HOUR`, `MULTI_SESSION` |
| `anomalies[].severity` | string | Mức độ: `LOW` / `MEDIUM` / `HIGH` / `CRITICAL` |
| `active_session_count` | integer | Số phiên đang hoạt động hiện tại |
| `failed_login_count_24h` | integer | Số lần đăng nhập thất bại trong 24h qua |

> Nếu không phát hiện bất thường: `risk_level = "SAFE"`, `anomalies = []`

---

## 9. Cấu trúc lỗi chung

Mọi lỗi đều trả về cấu trúc JSON thống nhất:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Mô tả lỗi bằng tiếng Việt",
    "details": {}
  }
}
```

### Bảng mã lỗi phổ biến

| HTTP | error_code | Ý nghĩa |
|---|---|---|
| `401` | `UNAUTHORIZED` | Không có token hoặc token không hợp lệ |
| `401` | `EXPIRED_ACCESS_TOKEN` | Access token đã hết hạn → cần gọi `/auth/refresh` |
| `401` | `INACTIVE_USER` | Tài khoản bị khoá |
| `403` | `FORBIDDEN_ACCESS` | Không đủ quyền thực hiện hành động |
| `404` | `USER_NOT_FOUND` | Người dùng không tồn tại |
| `404` | `SESSION_NOT_FOUND` | Phiên đăng nhập không tồn tại |
| `422` | `VALIDATION_ERROR` | Tham số không hợp lệ |
| `500` | `INTERNAL_SERVER_ERROR` | Lỗi máy chủ nội bộ |

---

## 10. Hướng dẫn tích hợp FE

### Cài đặt Axios interceptor chuẩn

```typescript
// src/services/http/client.ts
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  withCredentials: true, // Bắt buộc để gửi cookie refresh_token
})

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401) {
      // Thử refresh token
      try {
        const refreshRes = await axios.post('/api/v1/auth/refresh', {}, { withCredentials: true })
        const { access_token } = refreshRes.data
        // Cập nhật store và retry request gốc
        error.config.headers['Authorization'] = `Bearer ${access_token}`
        return api.request(error.config)
      } catch {
        // Refresh thất bại → về trang login
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)
```

### Luồng UI đề xuất cho trang Activity

```
[UserDetailPage]
  ├── Tab: Phiên đăng nhập
  │     GET /users/{id}/sessions
  │     → Hiển thị DataTable với cột: IP, Thiết bị, Thời gian, Trạng thái, [Nút Thu hồi]
  │     → Mỗi dòng: POST /users/{id}/sessions/{sid}/revoke
  │     → Nút "Thu hồi tất cả": POST /users/{id}/sessions/revoke-all
  │
  ├── Tab: Lịch sử đăng nhập
  │     GET /users/{id}/login-history?status=failed
  │     → Phân trang, lọc Success/Failed
  │     → Màu đỏ cho bản ghi failed
  │
  ├── Tab: Bảo mật & Bất thường
  │     GET /users/{id}/anomalies
  │     → Hiển thị badge risk_level (SAFE=xanh, LOW=vàng, MEDIUM=cam, HIGH=đỏ, CRITICAL=đỏ nháy)
  │     → Danh sách anomalies với icon theo severity
  │
  └── Hành động tài khoản
        POST /users/{id}/lock   → Hiện confirm dialog trước khi thực hiện
        POST /users/{id}/unlock → Không cần confirm
```

### Xử lý lỗi theo error_code

```typescript
function handleApiError(error: AxiosError) {
  const code = error.response?.data?.error?.code

  switch (code) {
    case 'SESSION_NOT_FOUND':
      toast.error('Phiên đăng nhập không tồn tại')
      break
    case 'USER_NOT_FOUND':
      toast.error('Không tìm thấy người dùng')
      break
    case 'FORBIDDEN_ACCESS':
      toast.error('Bạn không có quyền thực hiện hành động này')
      break
    default:
      toast.error('Có lỗi xảy ra. Vui lòng thử lại.')
  }
}
```

### Hiển thị Risk Level

```typescript
const RISK_BADGE = {
  SAFE:     { color: 'green',  label: 'An toàn',     icon: '✅' },
  LOW:      { color: 'blue',   label: 'Thấp',        icon: '🔵' },
  MEDIUM:   { color: 'yellow', label: 'Trung bình',  icon: '⚠️' },
  HIGH:     { color: 'orange', label: 'Cao',         icon: '🔴' },
  CRITICAL: { color: 'red',    label: 'Nguy hiểm',   icon: '🚨' },
} as const
```

### Hiển thị Anomaly Type

```typescript
const ANOMALY_LABELS = {
  BRUTE_FORCE:   'Tấn công dò mật khẩu',
  NEW_LOCATION:  'Địa điểm đăng nhập mới',
  UNUSUAL_HOUR:  'Đăng nhập ngoài giờ',
  MULTI_SESSION: 'Nhiều phiên đồng thời',
} as const
```

---

*Tài liệu tạo tự động — cập nhật lần cuối: 2024-06-27*
