# Authentication & Session Management API Documentation

This documentation describes the authentication system, endpoints, and integration flow for frontend developers.

## 1. Architecture Overview

Our backend implements a secure **JWT Access Token** + **HttpOnly Refresh Token** architecture with **Refresh Token Rotation (RTR)**. 

### Key Design Pillars:
*   **Short-lived Access Token**: Transmitted in the response body as a JSON Web Token (JWT). The frontend should store this in memory (e.g., in a React context or Zustand state) and include it in the `Authorization: Bearer <token>` header for all authenticated requests.
*   **Long-lived Refresh Token**: Stored in a secure, `HttpOnly`, `SameSite=Lax` cookie named `refresh_token` with an 8-day expiration. The frontend does not need to (and cannot) read or write this cookie directly; the browser handles it automatically for requests matching the cookie's path.
*   **Refresh Token Rotation (RTR)**: Every time `/api/v1/auth/refresh` is called, the backend issues a new access token *and* invalidates the old refresh token, replacing it with a new one in the `set-cookie` header.
*   **Security Breach Lineage Detection**: If an already-rotated/revoked refresh token is sent to `/refresh` (e.g., in the event of token theft or replay attacks), the backend instantly detects a lineage breach and **revokes all active sessions** belonging to that user. The user is forced to log in again.

---

## 2. API Reference

All routes are prefixed with `/api/v1`.

### A. Login
*   **Endpoint**: `POST /api/v1/auth/login`
*   **Description**: Authenticate with username and password.

#### Request Headers:
```http
Content-Type: application/json
```

#### Request Body:
```json
{
  "username": "admin",
  "password": "adminpassword"
}
```

#### Response (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```
*   **Set-Cookie Header**: The server attaches the `refresh_token` cookie:
    ```http
    Set-Cookie: refresh_token=ad57775fe0a16cde...; Max-Age=691200; Path=/; HttpOnly; SameSite=lax
    ```
    *Note: In production environments, `Secure` is automatically set to ensure the cookie is only transmitted over HTTPS.*

#### Error Responses:
*   `401 Unauthorized`:
    *   Invalid credentials:
        ```json
        {
          "success": false,
          "error": {
            "code": "INCORRECT_CREDENTIALS",
            "message": "Tên đăng nhập hoặc mật khẩu không chính xác"
          }
        }
        ```
    *   Inactive/Disabled account:
        ```json
        {
          "success": false,
          "error": {
            "code": "INACTIVE_USER",
            "message": "Tài khoản người dùng đã bị khóa hoặc chưa kích hoạt"
          }
        }
        ```

---

### B. Refresh Access Token (Token Rotation)
*   **Endpoint**: `POST /api/v1/auth/refresh`
*   **Description**: Uses the HttpOnly cookie to acquire a new short-lived access token and a rotated refresh token cookie.

#### Request Headers:
No authorization header is needed. The browser automatically attaches the `refresh_token` cookie.

#### Response (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```
*   **Set-Cookie Header**: Rotates the current cookie, providing a new `refresh_token` value.

#### Error Responses:
*   `401 Unauthorized`:
    *   Missing refresh token cookie:
        ```json
        {
          "success": false,
          "error": {
            "code": "MISSING_REFRESH_TOKEN",
            "message": "Thiếu token làm mới trong cookie"
          }
        }
        ```
    *   Expired session token:
        ```json
        {
          "success": false,
          "error": {
            "code": "SESSION_EXPIRED",
            "message": "Phiên đăng nhập đã hết hạn"
          }
        }
        ```
    *   Invalid or non-existent session token:
        ```json
        {
          "success": false,
          "error": {
            "code": "INVALID_SESSION",
            "message": "Phiên đăng nhập không hợp lệ"
          }
        }
        ```
    *   Security breach detected (reused token):
        ```json
        {
          "success": false,
          "error": {
            "code": "SECURITY_BREACH",
            "message": "Phát hiện xâm nhập bảo mật: Token đã được sử dụng lại. Tất cả các phiên đã bị thu hồi."
          }
        }
        ```

---

### C. Current User Profile
*   **Endpoint**: `GET /api/v1/auth/me`
*   **Description**: Retrieve details of the currently logged-in user.

#### Request Headers:
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response (200 OK):
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "username": "admin",
  "email": "admin@university.edu.vn",
  "is_active": true,
  "role": "super_admin"
}
```

#### Error Responses:
*   `401 Unauthorized`:
    *   Expired Access Token:
        ```json
        {
          "success": false,
          "error": {
            "code": "EXPIRED_ACCESS_TOKEN",
            "message": "Access token has expired"
          }
        }
        ```
    *   Invalid Access Token:
        ```json
        {
          "success": false,
          "error": {
            "code": "INVALID_ACCESS_TOKEN",
            "message": "Invalid access token"
          }
        }
        ```
    *   User Not Found:
        ```json
        {
          "success": false,
          "error": {
            "code": "USER_NOT_FOUND",
            "message": "User not found"
          }
        }
        ```
    *   Inactive/Disabled Account:
        ```json
        {
          "success": false,
          "error": {
            "code": "INACTIVE_USER",
            "message": "User account is inactive"
          }
        }
        ```

---

### D. List Active Devices / Sessions
*   **Endpoint**: `GET /api/v1/auth/devices`
*   **Description**: Get a list of all active sessions/devices for the authenticated user.

#### Request Headers:
```http
Authorization: Bearer <access_token>
```

#### Response (200 OK):
```json
[
  {
    "id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "ip_address": "127.0.0.1",
    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36...",
    "created_at": "2026-06-26T22:15:26.434Z",
    "expires_at": "2026-07-04T22:15:26.434Z",
    "is_current": true
  }
]
```
*   `is_current`: Flags if the device corresponds to the refresh token cookie attached to the current request.

#### Error Responses:
*   Same standard auth error responses as `GET /auth/me` (`EXPIRED_ACCESS_TOKEN`, `INVALID_ACCESS_TOKEN`, `USER_NOT_FOUND`, `INACTIVE_USER`).

---

### E. Revoke Device Session
*   **Endpoint**: `POST /api/v1/auth/devices/{device_id}/revoke`
*   **Description**: Invalidate a specific active session.

#### Request Headers:
```http
Authorization: Bearer <access_token>
```

#### Response (200 OK):
```json
{
  "success": true
}
```

#### Error Responses:
*   Same standard auth error responses as `GET /auth/me`.

---

### F. Logout (Current Session)
*   **Endpoint**: `POST /api/v1/auth/logout`
*   **Description**: Terminate the current session by revoking the refresh token in the database and deleting the `refresh_token` cookie.

#### Request Headers:
No authorization header is needed (the request is identified by the cookie).

#### Response (200 OK):
```json
{
  "success": true
}
```
*   **Set-Cookie Header**: Clears the cookie.

---

### G. Logout All Devices
*   **Endpoint**: `POST /api/v1/auth/logout-all`
*   **Description**: Invalidate every active refresh token belonging to the user and clear the local cookie.

#### Request Headers:
```http
Authorization: Bearer <access_token>
```

#### Response (200 OK):
```json
{
  "success": true
}
```

#### Error Responses:
*   Same standard auth error responses as `GET /auth/me`.

---

## 3. Standardized Error Codes Reference

All error responses strictly follow the envelope format below:
```json
{
  "success": false,
  "error": {
    "code": "<ERROR_CODE>",
    "message": "<Developer/User-facing message>",
    "details": {}
  }
}
```

### Bảng Tra Cứu Chi Tiết

| Mã Lỗi (Error Code) | Trạng Thái HTTP | Mô tả nguyên nhân |
| :--- | :--- | :--- |
| `INCORRECT_CREDENTIALS` | 401 Unauthorized | Tên đăng nhập hoặc mật khẩu không chính xác. |
| `INACTIVE_USER` | 401 Unauthorized | Tài khoản người dùng đã bị khóa hoặc chưa kích hoạt bởi quản trị viên. |
| `EXPIRED_ACCESS_TOKEN` | 401 Unauthorized | Chữ ký JWT access token đã hết hạn. FE cần thực hiện silent refresh. |
| `INVALID_ACCESS_TOKEN` | 401 Unauthorized | JWT access token không hợp lệ, sai định dạng hoặc lỗi chữ ký xác thực. |
| `USER_NOT_FOUND` | 401 Unauthorized | Không tìm thấy người dùng tương ứng với ID định danh trong access token. |
| `MISSING_REFRESH_TOKEN` | 401 Unauthorized | Cookie yêu cầu không chứa khóa `refresh_token`. |
| `INVALID_SESSION` | 401 Unauthorized | Giá trị băm của Refresh token không khớp/không tìm thấy trong database. |
| `SESSION_EXPIRED` | 401 Unauthorized | Phiên làm việc (Refresh token) đã hết hạn (Quá hạn 8 ngày). Người dùng phải re-login. |
| `SECURITY_BREACH` | 401 Unauthorized | Phát hiện sử dụng lại token cũ. Hủy toàn bộ các phiên hoạt động của tài khoản này. |
| `VALIDATION_ERROR` | 422 Unprocessable | Dữ liệu gửi lên không đúng định dạng. Chi tiết lỗi xem trong trường `details`. |
| `INTERNAL_SERVER_ERROR` | 500 Internal Error | Lỗi hệ thống phát sinh ở phía máy chủ. Thông tin chi tiết đã được ghi lại trong log. |

---

## 4. Frontend Integration Flow

```mermaid
sequenceDiagram
    autonumber
    actor User as User Agent (Browser)
    participant FE as Frontend Client (JS)
    participant API as Backend API Server
    
    Note over User, API: 1. Login Phase
    User->>FE: Enters credentials
    FE->>API: POST /auth/login {username, password}
    API-->>FE: Response: {access_token}
    Note right of API: Sets HttpOnly cookie: refresh_token
    FE->>FE: Stores access_token in memory
    
    Note over User, API: 2. Authenticated Requests
    FE->>API: GET /auth/me with Authorization: Bearer <access_token>
    API-->>FE: Response: User profile {role, email, ...}
    
    Note over User, API: 3. Token Expiration & Rotation (Axios Interceptor)
    FE->>API: GET /some-protected-endpoint (Expired access_token)
    API-->>FE: 401 Unauthorized (EXPIRED_ACCESS_TOKEN)
    FE->>API: POST /auth/refresh (Browser sends refresh_token cookie)
    API-->>FE: Response: {access_token}
    Note right of API: Rotates and sets new refresh_token cookie
    FE->>FE: Updates access_token in memory
    FE->>API: Re-tries GET /some-protected-endpoint
    API-->>FE: Response: Success data
```

### Axios Interceptor Reference Implementation
Below is a standard template for handling silent refreshes using Axios interceptors:

```typescript
import axios from 'axios';

let isRefreshing = false;
let failedQueue: any[] = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

const api = axios.create({
  baseURL: '/api/v1',
  withCredentials: true, // Crucial: sends the refresh token cookie
});

// Request interceptor to attach JWT
api.interceptors.request.use((config) => {
  const token = getAccessTokenFromMemory(); // Retrieve from React State / Zustand
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`;
  }
  return config;
}, (error) => Promise.reject(error));

// Response interceptor to handle 401 & trigger silent refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      const errorCode = error.response?.data?.error?.code;

      // Only attempt to refresh if the error is specifically due to an expired access token
      if (errorCode === 'EXPIRED_ACCESS_TOKEN') {
        if (isRefreshing) {
          return new Promise((resolve, reject) => {
            failedQueue.push({ resolve, reject });
          })
            .then((token) => {
              originalRequest.headers['Authorization'] = `Bearer ${token}`;
              return api(originalRequest);
            })
            .catch((err) => Promise.reject(err));
        }

        originalRequest._retry = true;
        isRefreshing = true;

        try {
          const refreshResponse = await axios.post('/api/v1/auth/refresh', {}, { withCredentials: true });
          const { access_token } = refreshResponse.data;
          
          saveAccessTokenInMemory(access_token); // Save to state manager
          
          processQueue(null, access_token);
          isRefreshing = false;
          
          originalRequest.headers['Authorization'] = `Bearer ${access_token}`;
          return api(originalRequest);
        } catch (refreshError) {
          processQueue(refreshError, null);
          isRefreshing = false;
          clearAccessTokenMemory();
          window.location.href = '/login'; // Redirect to login
          return Promise.reject(refreshError);
        }
      } else {
        // For other 401 errors (e.g. INACTIVE_USER, INVALID_ACCESS_TOKEN), do not refresh
        clearAccessTokenMemory();
        window.location.href = '/login';
        return Promise.reject(error);
      }
    }
    return Promise.reject(error);
  }
);
```
