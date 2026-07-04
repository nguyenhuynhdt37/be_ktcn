# Hướng dẫn tích hợp HTTP-only Cookies cho FE Admin (Xác thực người dùng)

Tài liệu này hướng dẫn cách cấu hình và tích hợp Frontend Admin với cơ chế quản lý Token xác thực bằng Cookie mới từ Backend.

---

## 1. Cấu hình Chung (Bắt buộc)

Khi backend phản hồi và yêu cầu trình duyệt thiết lập/gửi Cookies, Frontend bắt buộc phải bật thuộc tính `withCredentials: true` trên Axios Client hoặc `credentials: 'include'` trên Fetch API.

### Cấu hình Axios Instance
```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  withCredentials: true, // BẮT BUỘC: Tự động gửi và nhận Cookies trên trình duyệt
  headers: {
    'Content-Type': 'application/json',
  },
});
```

### Lưu ý cấu hình CORS (Môi trường)
Khi Frontend gửi request có `withCredentials: true`, Backend chỉ cho phép nếu:
1. Backend cấu hình CORS với `allow_credentials=True`.
2. Backend cấu hình cụ thể Domain của FE (ví dụ: `http://localhost:3000`, `http://localhost:5173`) thay vì dùng dấu sao `*` (Backend đã được cấu hình đúng).

---

## 2. Các Luồng Nghiệp Vụ Xác Thực

FE Admin quản lý 2 cookie: `access_token` (JWT truy cập ngắn hạn) và `refresh_token` (Token làm mới dài hạn).

### Đăng nhập (`POST /api/v1/auth/login`)
*   **Request Body:** Gửi `username` và `password` bình thường.
*   **FE Xử lý:** Khi nhận response thành công (`200 OK`), **không cần** tự lấy token từ response để lưu vào `localStorage` hay `sessionStorage` nữa. Trình duyệt đã tự động nhận và lưu Cookies an toàn. Chỉ cần redirect sang trang Dashboard.
*   **Các request gọi API tiếp theo:** Trình duyệt sẽ tự động gửi kèm cookie `access_token`. Bạn **không cần** thêm header `Authorization: Bearer <token>` nữa.

### Tự động làm mới Token (Refresh Token Interceptor)
Khi `access_token` hết hạn, API sẽ trả về lỗi `401 Unauthorized`. Chúng ta sử dụng Axios Interceptor để tự động gọi API làm mới token:

```typescript
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // Nếu lỗi 401 (Token hết hạn) và request chưa được thử lại
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        // Gọi API refresh token. Backend tự đọc refresh_token từ cookie
        // và trả về cặp cookie mới (access_token & refresh_token)
        await axios.post(
          `${api.defaults.baseURL}/api/v1/auth/refresh`,
          {},
          { withCredentials: true }
        );
        
        // Thử lại request ban đầu với cookie mới
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh token hết hạn -> Chuyển hướng người dùng về trang đăng nhập
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);
```

### Đăng xuất (`POST /api/v1/auth/logout`)
*   **FE Xử lý:** Gửi request POST đến `/api/v1/auth/logout`.
*   Backend sẽ gửi chỉ thị xóa cả hai cookie `access_token` và `refresh_token`. Sau đó FE chỉ cần xóa các State / Redux nội bộ và chuyển hướng về trang `/login`.
