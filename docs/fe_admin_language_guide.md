# Hướng dẫn Tích hợp Quản lý Ngôn ngữ (FE Admin)

Tài liệu này hướng dẫn chi tiết cho lập trình viên Frontend (FE) cách xây dựng giao diện quản lý Ngôn ngữ trong trang quản trị Admin dựa trên hệ thống API Backend mới xây dựng ở Phase 1.

---

## I. DANH SÁCH ENDPOINTS API

Tất cả các API Admin yêu cầu header xác thực: `Authorization: Bearer <access_token>`.

### 1. Admin APIs (Quản lý)

| Method | Endpoint | Chức năng | Body / Params | Phản hồi chính (200/201) |
| :--- | :--- | :--- | :--- | :--- |
| **GET** | `/api/v1/languages` | Lấy toàn bộ ngôn ngữ | Không | Danh sách ngôn ngữ (gồm cả inactive) |
| **GET** | `/api/v1/languages/{id}` | Lấy chi tiết một ngôn ngữ | Không | Thông tin chi tiết ngôn ngữ |
| **POST** | `/api/v1/languages` | Tạo mới ngôn ngữ | `LanguageCreate` | Thông tin ngôn ngữ vừa tạo (201) |
| **PUT** | `/api/v1/languages/{id}` | Cập nhật ngôn ngữ | `LanguageUpdate` | Thông tin ngôn ngữ sau cập nhật |
| **PATCH**| `/api/v1/languages/{id}/enable` | Bật hoạt động ngôn ngữ | Không | Thông tin ngôn ngữ (`is_active: true`) |
| **PATCH**| `/api/v1/languages/{id}/disable`| Tắt hoạt động ngôn ngữ | Không | Thông tin ngôn ngữ (`is_active: false`) |
| **PATCH**| `/api/v1/languages/{id}/set-default` | Đặt làm ngôn ngữ mặc định | Không | Thông tin ngôn ngữ (`is_default: true`) |
| **DELETE**| `/api/v1/languages/{id}` | Xóa mềm ngôn ngữ | Không | Không trả về body (204) |
| **PATCH**| `/api/v1/languages/{id}/restore` | Khôi phục ngôn ngữ đã xóa | Không | Thông tin ngôn ngữ (`deleted_at: null`) |
| **PUT**   | `/api/v1/languages/reorder` | Sắp xếp lại thứ tự (kéo thả) | `LanguageReorderRequest` | `{"success": true, "reordered": number}` |

### 2. Public Portal API (Dành cho trang chủ / ngoài Portal)
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
      "flag_icon": "/flags/vi.svg",
      "is_default": true
    }
  ]
  ```

---

## II. CHI TIẾT CẤU TRÚC DỮ LIỆU (SCHEMAS)

### 1. Request Body khi Tạo Mới (`POST /api/v1/languages`)
```json
{
  "code": "en",           // Bắt buộc. Chỉ chứa chữ thường a-z, tối đa 10 ký tự.
  "name": "English",      // Bắt buộc. Tên hiển thị chung. Tối đa 100 ký tự.
  "native_name": "English", // Bắt buộc. Tên bản địa. Tối đa 100 ký tự.
  "flag_icon": "/flags/en.svg", // Tùy chọn. Đường dẫn URL ảnh quốc kỳ.
  "is_default": false,    // Tùy chọn, mặc định: false.
  "is_active": true,      // Tùy chọn, mặc định: true.
  "sort_order": 0         // Tùy chọn, mặc định: 0. Phải >= 0.
}
```

### 2. Request Body khi Cập Nhật (`PUT /api/v1/languages/{id}`)
*Lưu ý: Không cho phép sửa trường `code` sau khi đã tạo để tránh ảnh hưởng đến định tuyến và dữ liệu dịch ở các phase sau.*
```json
{
  "name": "English Updated",
  "native_name": "English",
  "flag_icon": "/flags/en.svg",
  "is_default": false,
  "is_active": true,
  "sort_order": 5
}
```

### 3. Phản hồi đầy đủ từ Admin API (`LanguageResponse`)
```json
{
  "id": "c92df45c-6ca8-4b5d-bbe4-18f57de24743",
  "code": "en",
  "name": "English",
  "native_name": "English",
  "flag_icon": "/flags/en.svg",
  "is_default": false,
  "is_system": true,
  "is_active": true,
  "sort_order": 1,
  "created_at": "2026-06-30T15:48:10Z",
  "updated_at": "2026-06-30T15:48:10Z",
  "deleted_at": null // Sẽ có giá trị timestamp nếu ngôn ngữ đã bị xóa mềm
}
```

### 4. Request Body khi Reorder kéo thả (`PUT /api/v1/languages/reorder`)
```json
{
  "items": [
    {
      "id": "c92df45c-6ca8-4b5d-bbe4-18f57de24743",
      "sort_order": 1
    },
    {
      "id": "b9ae3394-9942-4dc8-90c9-fed73bd09c67",
      "sort_order": 2
    }
  ]
}
```

---

## III. HƯỚNG DẪN XÂY DỰNG GIAO DIỆN (FE ADMIN UX/UI)

### 1. Trang Danh Sách Ngôn Ngữ (Languages List)
- **Bảng dữ liệu (Table)** hiển thị các cột:
  - **Quốc kỳ**: Hiển thị ảnh quốc kỳ nhỏ (icon/thumbnail) từ `flag_icon` URL. Nếu rỗng, hiển thị placeholder mặc định.
  - **Tên ngôn ngữ**: Hiển thị dạng `Name (Native Name)` (ví dụ: `English (English)` hoặc `Vietnamese (Tiếng Việt)`).
  - **Mã ngôn ngữ**: `code` (ví dụ: `vi`, `en`).
  - **Thứ tự sắp xếp**: `sort_order`.
  - **Mặc định**: Sử dụng thẻ nhãn (Badge/Tag) nổi bật hoặc biểu tượng Ngôi sao/Checkmark màu vàng cho ngôn ngữ có `is_default: true`.
  - **Trạng thái**: Switch toggle (Bật/Tắt) liên kết với cột `is_active`.
  - **Hành động**: Nút Sửa (Edit icon) và nút Xóa (Trash icon).
- **Quy tắc UI/UX đặc biệt**:
  - Đối với bản ghi đang là **Mặc định** (`is_default = true`):
    - Khóa Switch toggle trạng thái (luôn là bật, không cho phép tắt).
    - Ẩn hoặc disable nút Xóa (không được phép xóa ngôn ngữ mặc định).
  - Đối với bản ghi là **Hệ thống** (`is_system = true`):
    - Khóa hoặc disable nút Xóa (các ngôn ngữ cốt lõi như vi, en, lo không được phép xóa khỏi hệ thống).
    - Khóa việc chỉnh sửa `code` ngôn ngữ trong mọi trường hợp.
  - **Kéo thả sắp xếp (Drag & Drop Reorder)**:
    - Cho phép người dùng kéo thả các dòng trong bảng để thay đổi thứ tự hiển thị.
    - Sau khi người dùng kết thúc kéo thả, tính toán lại giá trị `sort_order` cho các bản ghi và gọi API `PUT /api/v1/languages/reorder` để cập nhật đồng loạt thứ tự mới xuống DB.
  - Thêm checkbox hoặc bộ lọc: `"Hiển thị ngôn ngữ đã xóa"` phục vụ admin khôi phục bản ghi đã xóa mềm. Khi bật bộ lọc này, các bản ghi có `deleted_at != null` sẽ hiển thị và đi kèm nút **Khôi phục** (Restore icon).

### 2. Popup/Form Thêm mới hoặc Chỉnh sửa Ngôn ngữ
- **Trường nhập liệu**:
  - Tên, Tên bản địa, Mã ngôn ngữ (chỉ khi tạo).
  - **Ảnh quốc kỳ (`flag_icon`)**: Nhập URL ảnh trực tiếp hoặc tích hợp thư viện Media chọn ảnh SVG/PNG.
- **Validation phía Client (Client-Side Validation)**:
  - Trường **Mã ngôn ngữ (`code`)**:
    - Input: Chỉ cho phép nhập chữ thường (a-z). Có thể tự động chuyển đổi chữ hoa nhập vào thành chữ thường trên UI.
    - Không cho nhập khoảng trắng hoặc ký tự đặc biệt.
    - Giới hạn tối đa 10 ký tự.
  - Trường **Thứ tự sắp xếp (`sort_order`)**:
    - Input kiểu Number, thuộc tính `min="0"`, không cho phép nhập số âm.
- **Ràng buộc khi cập nhật**:
  - Khi sửa ngôn ngữ, trường `code` nên được đặt ở trạng thái `disabled` (chỉ đọc).

---

## IV. XỬ LÝ LỖI PHÍA CLIENT (ERROR HANDLING)

Khi Backend trả về mã lỗi HTTP khác 200/201, FE cần bắt và hiển thị thông báo thân thiện cho quản trị viên:

### 1. Lỗi Validation đầu vào (HTTP `422 Unprocessable Entity`)
- Backend trả về danh sách chi tiết các trường bị lỗi dưới định dạng:
  ```json
  {
    "success": false,
    "error": {
      "code": "VALIDATION_ERROR",
      "message": "Dữ liệu đầu vào không hợp lệ",
      "details": {
        "body.code": "String should match pattern '^[a-z]+$'",
        "body.sort_order": "Input should be greater than or equal to 0"
      }
    }
  }
  ```
- **Xử lý**: Map các thông báo lỗi này hiển thị ngay dưới ô nhập liệu tương ứng trên Form (cắt bỏ tiền tố `body.` khi đối chiếu trường).

### 2. Lỗi nghiệp vụ không được phép (HTTP `400 Bad Request`)
- Xảy ra khi cố gắng xóa hoặc vô hiệu hóa ngôn ngữ mặc định.
- **Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "BAD_REQUEST",
      "message": "Không thể xóa ngôn ngữ mặc định",
      "details": {}
    }
  }
  ```
- **Xử lý**: Hiển thị thông báo Toast thông báo lỗi dạng Warning/Error trên góc màn hình với nội dung `message`.

### 3. Lỗi trùng lặp mã ngôn ngữ (HTTP `409 Conflict`)
- Xảy ra khi cố tạo mới một ngôn ngữ có mã `code` đã tồn tại trong hệ thống (kể cả trong các bản ghi đã xóa mềm).
- **Response**:
  ```json
  {
    "success": false,
    "error": {
      "code": "CONFLICT",
      "message": "Mã ngôn ngữ 'vi' đã tồn tại",
      "details": {}
    }
  }
  ```
- **Xử lý**: Hiển thị thông báo lỗi ngay ô nhập liệu "Mã ngôn ngữ" hoặc bắn Toast thông báo.

---

## V. LUỒNG TÁC VỤ ĐẶC BIỆT: THAY ĐỔI NGÔN NGỮ MẶC ĐỊNH
1. Khi Admin nhấn vào biểu tượng thiết lập mặc định của một ngôn ngữ (không phải ngôn ngữ mặc định hiện tại).
2. FE hiển thị Popup xác nhận: *"Bạn có chắc chắn muốn thay đổi ngôn ngữ mặc định của hệ thống sang [Tên ngôn ngữ] không?"*.
3. Khi người dùng xác nhận, gọi API: `PATCH /api/v1/languages/{id}/set-default`.
4. Khi thành công, load lại danh sách ngôn ngữ. Bản ghi ngôn ngữ mặc định mới sẽ tự động được kích hoạt và hiển thị nhãn "Mặc định", trong khi ngôn ngữ mặc định cũ sẽ mất nhãn mặc định nhưng vẫn hoạt động bình thường.
