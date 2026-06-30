# Hướng dẫn Tích hợp Ngôn ngữ phía Portal (FE Client)

Tài liệu này hướng dẫn lập trình viên Frontend Portal (FE Client) cách tích hợp API ngôn ngữ công khai để hiển thị danh sách chuyển đổi ngôn ngữ (Language Switcher) và cách truyền thông tin ngôn ngữ khi gọi các API nghiệp vụ khác.

---

## I. API ENDPOINT CÔNG KHAI

Để lấy danh sách các ngôn ngữ đang được kích hoạt và cho phép hiển thị trên trang chủ Portal:

- **Method**: `GET`
- **Endpoint**: `/api/v1/portal/languages`
- **Xác thực**: **Không yêu cầu Token** (Public API).
- **Phản hồi mẫu (HTTP 200)**:
  ```json
  [
    {
      "id": "ab7a1d12-1f3c-47bc-88a9-456578a1bc23",
      "code": "vi",
      "name": "Vietnamese",
      "native_name": "Tiếng Việt",
      "flag_id": null,
      "flag_url": null,
      "is_default": true
    },
    {
      "id": "e92df45c-6ca8-4b5d-bbe4-18f57de24743",
      "code": "en",
      "name": "English",
      "native_name": "English",
      "flag_id": "46976a6f-3adb-4db1-a583-ff0af87f8baf",
      "flag_url": "http://localhost:9000/cms/flags/en.svg",
      "is_default": false
    }
  ]
  ```

---

## II. HƯỚNG DẪN TÍCH HỢP TRÊN FRONTEND CLIENT

### 1. Luồng Xác định Ngôn ngữ Hiện tại (Current Language)
Khi người dùng truy cập trang Portal, FE cần xác định ngôn ngữ hiển thị theo thứ tự ưu tiên sau:
1. **Cookie** hoặc **localStorage**: Kiểm tra xem trước đó người dùng có chủ động chọn ngôn ngữ nào không (ví dụ: cookie `NEXT_LOCALE` hoặc local storage `lang`).
2. **Ngôn ngữ hệ thống mặc định**: Nếu chưa có lựa chọn lưu trữ, gọi API `/api/v1/portal/languages` và tìm bản ghi có `"is_default": true` để làm ngôn ngữ hiển thị mặc định.

> [!TIP]
> **Khuyên dùng Cookie**: Đối với các ứng dụng SSR (Next.js, Remix, v.v.), việc lưu ngôn ngữ vào **Cookie** là bắt buộc để Server có thể đọc ngay trong Request Header và trả về HTML đúng ngôn ngữ ngay lập tức, tránh hiện tượng nháy màn hình (Layout Shift) khi dịch ở phía Client.

### 2. Xây dựng Bộ chuyển đổi Ngôn ngữ (Language Switcher)
- Gọi API `GET /api/v1/portal/languages` khi khởi tạo ứng dụng để render danh sách lựa chọn trên Menu Header.
- **UI Render**:
  - Hiển thị ảnh quốc kỳ lấy từ `flag_url` cạnh tên bản địa (`native_name`) để tối ưu trải nghiệm người dùng (ví dụ: `flag_url` render trong thẻ `<img>`). Nếu `flag_url` là null, FE có thể render ảnh cờ placeholder mặc định.
- **Hành động chuyển đổi**:
  - Khi người dùng chọn một ngôn ngữ mới:
    1. Cập nhật cookie/localStorage (ví dụ: `document.cookie = "locale=en; path=/; max-age=31536000"`).
    2. Reload lại trang hoặc cập nhật State quản lý đa ngôn ngữ của ứng dụng.
    3. Reload lại các API lấy dữ liệu nghiệp vụ (Tin tức, Danh mục, Menu) theo mã ngôn ngữ mới chọn.

### 3. Cách gọi các API nghiệp vụ đa ngôn ngữ (Phase tiếp theo)
Sau khi hoàn thành Phase 1, các Phase tiếp theo sẽ triển khai dịch nội dung cho Article, Category, Menu. Khi đó, để lấy dữ liệu đúng ngôn ngữ đã chọn, FE Client cần truyền mã ngôn ngữ lên Backend qua một trong các phương thức sau:

#### Phương án 1: Sử dụng HTTP Header (Khuyên dùng)
Gửi kèm header `Accept-Language` trong tất cả các request API:
```http
GET /api/v1/articles HTTP/1.1
Host: api.example.com
Accept-Language: en
```

#### Phương án 2: Sử dụng Query Parameter
Truyền tham số `lang` trực tiếp trên URL:
```http
GET /api/v1/articles?lang=en
```
