# Hướng dẫn Tích hợp Quản lý Ngôn ngữ (FE Admin)

Tài liệu này hướng dẫn lập trình viên Frontend (FE) tích hợp và xây dựng giao diện quản lý Ngôn ngữ trong trang quản trị Admin dựa trên hệ thống API Backend Phase 1 và các ràng buộc nghiệp vụ thực tế của trường.

> [!IMPORTANT]
> **Ràng buộc nghiệp vụ**: Website trường học có cấu trúc đa ngôn ngữ cố định và giao diện cần biên dịch tĩnh (tĩnh hóa UI, menu, validation, SEO). Do đó, **Admin KHÔNG có quyền Thêm mới, Chỉnh sửa thông tin cốt lõi (Mã code, Tên) hoặc Xóa ngôn ngữ**. Giao diện chỉ cho phép Bật/Tắt hoạt động, thiết lập ngôn ngữ mặc định và Kéo thả sắp xếp thứ tự hiển thị của 3 ngôn ngữ hệ thống sẵn có:
> - 🇻🇳 **Tiếng Việt (`vi`)** (Mặc định ban đầu)
> - 🇬🇧 **Tiếng Anh (`en`)**
> - 🇱🇦 **Tiếng Lào (`lo`)**

---

## I. DANH SÁCH ENDPOINTS API KHẢ DỤNG

Tất cả các API Admin yêu cầu header xác thực: `Authorization: Bearer <access_token>`.

### 1. Admin APIs (Quản lý)

| Method | Endpoint | Chức năng | Body / Params | Phản hồi chính (200) |
| :--- | :--- | :--- | :--- | :--- |
| **GET** | `/api/v1/languages` | Lấy danh sách ngôn ngữ hiện có | Không | Danh sách 3 ngôn ngữ hệ thống |
| **PATCH**| `/api/v1/languages/{id}/enable` | Bật hoạt động ngôn ngữ | Không | Thông tin ngôn ngữ (`is_active: true`) |
| **PATCH**| `/api/v1/languages/{id}/disable`| Tắt hoạt động ngôn ngữ | Không | Thông tin ngôn ngữ (`is_active: false`) |
| **PATCH**| `/api/v1/languages/{id}/set-default` | Đặt làm ngôn ngữ mặc định | Không | Thông tin ngôn ngữ (`is_default: true`) |
| **PUT**   | `/api/v1/languages/reorder` | Sắp xếp lại thứ tự (kéo thả) | `LanguageReorderRequest` | `{"success": true, "reordered": number}` |

*(Lưu ý: Các API tạo mới POST, chỉnh sửa PUT, xóa DELETE và khôi phục PATCH restore của module ngôn ngữ đã được cấu hình ẩn và không tích hợp trên giao diện Admin).*

### 2. Public Portal API (Dành cho Client / Portal)
- **Endpoint**: `GET /api/v1/portal/languages`
- **Xác thực**: Không yêu cầu token.
- **Dữ liệu trả về**: Danh sách ngôn ngữ đang hoạt động (`is_active = true`), chỉ chứa các trường tối giản:
  ```json
  [
    {
      "id": "uuid-string",
      "code": "vi",
      "name": "Vietnamese",
      "native_name": "Tiếng Việt",
      "flag_url": "http://localhost:9000/cms/flags/vi.svg",
      "is_default": true
    }
  ]
  ```

---

## II. CHI TIẾT CẤU TRÚC DỮ LIỆU (SCHEMAS)

### 1. Phản hồi đầy đủ từ Admin API (`LanguageResponse`)
```json
{
  "id": "c92df45c-6ca8-4b5d-bbe4-18f57de24743",
  "code": "en",
  "name": "English",
  "native_name": "English",
  "flag_id": "46976a6f-3adb-4db1-a583-ff0af87f8baf",
  "flag_url": "http://localhost:9000/cms/flags/en.svg",
  "is_default": false,
  "is_system": true,
  "is_active": true,
  "sort_order": 10,
  "created_at": "2026-06-30T15:48:10Z",
  "updated_at": "2026-06-30T15:48:10Z",
  "deleted_at": null
}
```

### 2. Request Body khi Reorder kéo thả (`PUT /api/v1/languages/reorder`)
```json
{
  "items": [
    {
      "id": "c92df45c-6ca8-4b5d-bbe4-18f57de24743",
      "sort_order": 0
    },
    {
      "id": "b9ae3394-9942-4dc8-90c9-fed73bd09c67",
      "sort_order": 10
    }
  ]
}
```

---

## III. HƯỚNG DẪN XÂY DỰNG GIAO DIỆN (FE ADMIN UX/UI)

### 1. Trang Cấu hình Ngôn Ngữ (Languages List)
Giao diện quản lý ngôn ngữ hiển thị dưới dạng một bảng dữ liệu đơn giản, tích hợp tính năng kéo thả:

- **Bảng dữ liệu (Table)** hiển thị các cột:
  - **Kéo thả**: Cột chứa icon kéo thả (`GripVertical`) ở đầu hàng để biểu thị dòng có thể kéo.
  - **Quốc kỳ**: Hiển thị ảnh quốc kỳ nhỏ bo góc mượt mà từ `flag_url`. Nếu rỗng, hiển thị icon quả địa cầu mặc định.
  - **Tên ngôn ngữ**: Hiển thị dạng `Name (Native Name)` (ví dụ: `English (English)`).
  - **Mã ngôn ngữ**: `code` (ví dụ: `vi`, `en`) dạng nhãn nhỏ.
  - **Thứ tự sắp xếp**: Cột `sort_order` hiển thị dạng số.
  - **Mặc định**: Sử dụng thẻ nhãn (Badge) màu vàng/nổi bật hoặc Ngôi sao màu vàng cho ngôn ngữ có `is_default: true`. Các ngôn ngữ khác hiển thị icon Ngôi sao màu xám nhạt (khi click sẽ mở AlertDialog đổi mặc định).
  - **Trạng thái**: Switch toggle (Bật/Tắt) liên kết trực tiếp với trường `is_active`.

- **Quy tắc UI/UX đặc biệt**:
  - **Chặn vô hiệu hóa ngôn ngữ mặc định**: Đối với bản ghi đang là **Mặc định** (`is_default = true`), Switch toggle trạng thái hoạt động phải bị **khóa/vô hiệu hóa** (luôn ở trạng thái bật).
  - **Kéo thả sắp xếp (Drag & Drop Reorder)**:
    - Sử dụng thư viện kéo thả của dự án (`dnd-kit` với `SortableContext` và chiến lược `verticalListSortingStrategy`).
    - Sau khi người dùng kết thúc kéo thả, tính toán lại giá trị `sort_order` (ví dụ: `index * 10`) và gửi yêu cầu cập nhật đồng loạt qua API `PUT /api/v1/languages/reorder`.
    - Hiển thị thông báo Toast thành công hoặc Spinner "Đang lưu..." nhỏ ở góc màn hình khi quá trình lưu ngầm đang diễn ra.

---

## IV. LUỒNG TÁC VỤ ĐẶC BIỆT: THAY ĐỔI NGÔN NGỮ MẶC ĐỊNH
1. Khi Admin nhấn vào biểu tượng Ngôi sao của một ngôn ngữ không mặc định.
2. FE hiển thị Popup xác nhận: *"Bạn có chắc chắn muốn thay đổi ngôn ngữ mặc định của hệ thống sang [Tên ngôn ngữ] không?"*.
3. Khi người dùng xác nhận, gọi API: `PATCH /api/v1/languages/{id}/set-default`.
4. Khi thành công, load lại danh sách ngôn ngữ. Bản ghi ngôn ngữ mặc định mới sẽ tự động kích hoạt và hiển thị nhãn "Mặc định", trong khi ngôn ngữ mặc định cũ sẽ mất nhãn mặc định nhưng vẫn hoạt động bình thường.
