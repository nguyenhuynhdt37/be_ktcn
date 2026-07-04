# Hướng dẫn tích hợp HTTP-only Cookies cho FE Portal / Client (Theo dõi đếm lượt xem)

Tài liệu này hướng dẫn cách cấu hình và tích hợp Frontend Client (Portal) với cơ chế theo dõi lượt xem (Guest UUID) bằng Cookie mới từ Backend để chống spam view bài viết/lịch tuần.

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

## 2. Theo Dõi Lượt Xem Qua Cookie `guest_uuid` và IP

FE Client dùng cookie `guest_uuid` và IP máy khách để đếm view bài viết và tránh việc F5 tăng view spam.

### Quy tắc đếm view của Backend:
1.  **Theo Guest UUID (24 giờ):** Mỗi thiết bị/trình duyệt chỉ được tính tối đa 1 lượt xem cho một bài viết trong vòng **24 giờ**.
2.  **Theo IP máy khách (3 phút):** Trong trường hợp người dùng cố tình xóa cookie để lấy `guest_uuid` mới hòng spam view, Backend sẽ kiểm tra IP của họ. Mỗi IP chỉ được phép tăng lượt xem tối đa 1 lần mỗi **3 phút** (giới hạn ngắn này giúp tránh ảnh hưởng đến những người dùng thực tế khác dùng chung một mạng Wi-Fi công cộng/NAT IP).

### Tự động xử lý Cookie
*   FE Portal **không cần tự sinh UUID** hay viết code quản lý lưu trữ cookie này.
*   Lần đầu tiên người đọc xem một bài viết (ví dụ: `GET /api/v1/portal/articles/{slug}`), Backend phát hiện thiếu `guest_uuid` trong cookie request, tự sinh một UUID duy nhất và trả về qua header `Set-Cookie` với thời hạn **1 năm**.
*   Trình duyệt tự lưu cookie này và tự gửi kèm trên các request lấy chi tiết bài viết tiếp theo.

### Yêu cầu đối với FE Portal
Đảm bảo Axios / Fetch Client gọi đến API lấy chi tiết bài viết (`GET /api/v1/portal/articles/{slug}`) đã bật thuộc tính `withCredentials: true` (hoặc `credentials: 'include'`). Trình duyệt sẽ tự động quản lý toàn bộ việc nhận và gửi mã này lên máy chủ.
