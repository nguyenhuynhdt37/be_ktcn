# Giải thích: Tại sao Menu Item hiển thị "[Đã xóa]" trên Frontend

Tài liệu này giải thích cơ chế kiểm tra và hiển thị trạng thái của các tài nguyên liên kết (Target) trong module Menu giúp Frontend Developer hiểu và xử lý UI tương ứng.

---

## 1. Bản chất vấn đề
Mỗi mục trong menu (`MenuItem`) có thể liên kết tới một tài nguyên động khác trong hệ thống (Polymorphic Association) thông qua cặp trường:
*   `target_type`: Loại tài nguyên (ví dụ: `CATEGORY`, `ARTICLE`, `PAGE`, `DEPARTMENT`...)
*   `target_id`: ID của tài nguyên liên kết.

Khi một tài nguyên (ví dụ: danh mục học thuật, bài viết tin tức, phòng ban...) bị **xóa mềm (soft deleted)** hoặc **xóa cứng (hard deleted)** khỏi hệ thống, các Menu Item cũ vẫn lưu `target_id` cũ sẽ trở thành **liên kết chết (broken links)**.

---

## 2. Cách Backend xử lý và trả về
Để bảo toàn dữ liệu cấu hình menu của Admin và không gây crash hệ thống, thay vì báo lỗi không tìm thấy, Backend tích hợp bộ giải quyết liên kết (`TargetResolver`) tự động kiểm tra trạng thái của các tài nguyên đích:

*   Nếu tài nguyên liên kết **đã bị xóa** (hoặc không tồn tại):
    *   Trường `target_info` trong JSON response sẽ trả về cấu trúc đặc biệt:
        ```json
        {
          "id": "uuid-cua-tai-nguyen-da-xoa",
          "type": "CATEGORY", // hoặc ARTICLE, DEPARTMENT...
          "name": "[Đã xóa]", // Tiêu đề hiển thị mặc định
          "status": "DELETED" // Trạng thái DELETED để phân biệt
        }
        ```
*   Nhờ vậy, Frontend có thể nhận biết chính xác liên kết nào đã hỏng.

---

## 3. Cách Frontend xử lý hiển thị

### A. Trên trang CMS Admin (Cấu hình Menu)
*   **Dấu hiệu**: Kiểm tra nếu `target_info.status === 'DELETED'` hoặc `target_info.name === '[Đã xóa]'`.
*   **Hiển thị đề xuất**:
    *   Hiển thị badge màu đỏ **"Liên kết đã bị xóa"** hoặc **"[Đã xóa]"** kế bên tiêu đề của Menu Item trong cây kéo thả.
    *   Vô hiệu hóa việc click xem thử, hiển thị nút cảnh báo yêu cầu Admin cập nhật lại liên kết mới cho Menu Item đó để tránh liên kết hỏng ngoài Website.
    *   *UI Mockup*:
        > 📁 Chương trình đào tạo (Trỏ tới: `Tin học Đại cương` [Đã xóa] ⚠️)

### B. Trên trang Portal (Website công khai)
*   **Hành vi**:
    *   Các liên kết chết (có `status: 'DELETED'`) không nên điều hướng người dùng tới trang lỗi 404.
    *   Frontend có thể ẩn hoàn toàn Menu Item đó đi nếu phát hiện `target_info.status === 'DELETED'`.
    *   Hoặc chuyển đổi link thành dạng Label thường (không có link điều hướng `has_link = false`).
