# Tài liệu tổng hợp API mới và thay đổi dành cho Front-End (FE)

Tài liệu này tổng hợp toàn bộ các thay đổi về đường dẫn API, API mới và cấu trúc dữ liệu mới sau đợt refactor hệ thống (bao gồm các module: **Tag**, **Media**, **Language**, **Health**, và **Degree**).

---

## 1. Module TAG (API Mới)

### **Kiểm tra trùng lặp Slug của Tag (Check Tag Slug)**
API dùng để kiểm tra xem slug mà người dùng nhập đã tồn tại trong hệ thống chưa trước khi tạo hoặc cập nhật Tag.

* **URL:** `/api/v1/admin/tags/check-slug`
* **Method:** `GET`
* **Headers:** `Authorization: Bearer <token>`
* **Query Parameters:**
  * `slug` *(string, bắt buộc)*: Slug cần kiểm tra (ví dụ: `hoc-bong`).
  * `exclude_id` *(UUID, optional)*: ID của Tag hiện tại. **Bắt buộc truyền khi cập nhật Tag** để tránh hệ thống tự báo trùng với chính nó.
  * `lang` *(string, default: "vi")*: Ngôn ngữ kiểm tra trùng lặp.
* **Response (200 OK):**
  ```json
  {
    "exists": true,                         // true = bị trùng, false = khả dụng
    "suggested_slug": "hoc-bong-add0f10d"   // Gợi ý slug mới không trùng nếu exists là true
  }
  ```

---

## 2. Module MEDIA (Thay đổi đường dẫn API)

Toàn bộ các API quản lý file và folder đã được chuyển sang tiền tố quản trị `/admin/media` để đồng bộ hóa với hệ thống.

* **Thay đổi Prefix:** từ `/api/v1/media` ➡️ `/api/v1/admin/media`
* **Headers:** `Authorization: Bearer <token>` cho tất cả các API.

### **Bảng danh sách API Media mới:**

| Chức năng | Method | Endpoint mới | Request Body / Params | Response (200 OK) |
| :--- | :--- | :--- | :--- | :--- |
| **Lấy danh sách file/folder** | `GET` | `/api/v1/admin/media` | Query: `parent_id` (UUID, optional) | Mảng `MediaItemResponse[]` |
| **Tạo thư mục mới** | `POST` | `/api/v1/admin/media/folders` | JSON: `{"name": "string", "parent_id": "UUID/null"}` | `MediaItemResponse` |
| **Upload tập tin** | `POST` | `/api/v1/admin/media/upload` | Form-Data: `file` (Binary), `parent_id` (UUID, optional) | `MediaItemResponse` |
| **Tải file về máy (Download)** | `GET` | `/api/v1/admin/media/{media_id}/download` | Path: `media_id` (UUID) | Binary Stream |
| **Lấy URL trực tiếp của file** | `GET` | `/api/v1/admin/media/{media_id}/url` | Path: `media_id` (UUID) | `{"url": "string"}` |
| **Đổi tên file hoặc folder** | `POST` | `/api/v1/admin/media/{media_id}/rename` | Path: `media_id` (UUID)<br>JSON: `{"name": "string"}` | `MediaItemResponse` |
| **Di chuyển file hoặc folder** | `POST` | `/api/v1/admin/media/{media_id}/move` | Path: `media_id` (UUID)<br>JSON: `{"parent_id": "UUID/null"}` | `MediaItemResponse` |
| **Sao chép file (Copy)** | `POST` | `/api/v1/admin/media/{media_id}/copy` | Path: `media_id` (UUID)<br>JSON: `{"dest_parent_id": "UUID/null"}` | `MediaItemResponse` |
| **Xóa file hoặc folder** | `DELETE`| `/api/v1/admin/media/{media_id}` | Path: `media_id` (UUID) | `{"success": true}` |
| **Sinh S3 Presigned Upload URL** | `POST` | `/api/v1/admin/media/presigned-upload` | Query: `filename` (str), `content_type` (str), `expires_in` (int) | `{"url": "str", "fields": {...}, "expires_in": int}` |
| **Sinh Presigned Download URL** | `GET` | `/api/v1/admin/media/{media_id}/presigned-download` | Path: `media_id` (UUID)<br>Query: `expires_in` (int) | `{"url": "str"}` |

* **Định dạng cấu trúc `MediaItemResponse`:**
  ```json
  {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "name": "anh_tuyen_sinh.png",
    "is_folder": false,
    "parent_id": null,
    "object_key": "media/2026/07/03/anh_tuyen_sinh.png",
    "thumbnail_key": null,
    "bucket": "university-media",
    "mime_type": "image/png",
    "size": 204800,
    "checksum": "md5-checksum-string",
    "width": 1200,
    "height": 900,
    "created_at": "2026-07-03T00:24:23Z",
    "updated_at": "2026-07-03T00:24:23Z"
  }
  ```

---

## 3. Module LANGUAGE (Thay đổi đường dẫn API Admin)

Đồng bộ tiền tố của các API quản lý ngôn ngữ.

* **Prefix quản trị (Admin APIs):** Chuyển từ `/api/v1/languages` ➡️ `/api/v1/admin/languages`
* **Prefix công khai (Client/Portal APIs):** Giữ nguyên ở `/api/v1/portal/languages`

---

## 4. Module HEALTH (Không thay đổi đường dẫn API)

API kiểm tra tình trạng kết nối cơ sở dữ liệu và hệ thống lưu trữ cache.

* **URL:** `/health` (Nằm ở root level)
* **Method:** `GET`
* **Headers:** Không yêu cầu
* **Response (200 OK):**
  ```json
  {
    "success": true,
    "status": "healthy",
    "details": {
      "postgres": "healthy",
      "redis": "healthy"
    }
  }
  ```

---

## 5. Module DEGREE (Thay đổi đường dẫn API)

Đồng bộ hóa cấu trúc prefix cho các API Học vị (Degrees) theo quy chuẩn.

* **Prefix quản trị (Admin APIs):** Chuyển từ `/api/v1/degrees` ➡️ `/api/v1/admin/degrees`
* **Prefix công khai (Client/Portal APIs):** Chuyển từ `/api/v1/portal` ➡️ `/api/v1/portal/degrees`

### **Chi tiết API Degree:**

#### **A. Public Client / Portal API (Không yêu cầu xác thực)**
Lấy danh sách các Học vị hoạt động phẳng đã được dịch ngôn ngữ phù hợp.
* **URL:** `/api/v1/portal/degrees`
* **Method:** `GET`
* **Query Parameters:**
  * `lang` *(string, default: "vi")*: Ngôn ngữ hiển thị (`vi`/`en`).
  * `Accept-Language` *(header, optional)*: Fallback ngôn ngữ nếu param `lang` trống.
* **Response (200 OK):** Mảng chứa `DegreePortalResponse[]`
  ```json
  [
    {
      "id": "acb9b98c-3f64-4ce9-a1b1-fa2de152be6e",
      "name": "Doctor of Philosophy",
      "abbreviation": "PhD",
      "sort_order": 0
    }
  ]
  ```

#### **B. Admin API (Yêu cầu Header: `Authorization: Bearer <token>`)**
Lấy toàn bộ danh sách Học vị đầy đủ cấu trúc bản dịch phục vụ quản trị.
* **URL:** `/api/v1/admin/degrees`
* **Method:** `GET`
* **Response (200 OK):** Mảng chứa `DegreeAdminResponse[]`
  ```json
  [
    {
      "id": "acb9b98c-3f64-4ce9-a1b1-fa2de152be6e",
      "sort_order": 0,
      "is_active": true,
      "name": "Tiến sĩ",                          // Flat default translation (vi)
      "abbreviation": "TS",                       // Flat default abbreviation (vi)
      "translations": {
        "vi": {
          "name": "Tiến sĩ",
          "abbreviation": "TS"
        },
        "en": {
          "name": "Doctor of Philosophy",
          "abbreviation": "PhD"
        }
      }
    }
  ]
  ```
