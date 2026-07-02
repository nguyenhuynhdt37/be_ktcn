# Hướng dẫn tích hợp Translation Context dành cho Frontend (FE)

Tài liệu này hướng dẫn chi tiết cách Frontend (FE) tích hợp tham số `context` khi gọi các API dịch thuật tự động của Backend. Việc truyền đúng ngữ cảnh giúp AI dịch chính xác, tự nhiên và bảo toàn cấu trúc dữ liệu tốt nhất.

---

## 1. Danh sách các Translation Context hỗ trợ

Khi gọi các API dịch thuật, FE có thể truyền thêm trường `context` (kiểu chuỗi) với một trong các giá trị Enum sau:

| Context Enum | Sử dụng cho | Mô tả & Quy tắc Dịch của AI |
|:---|:---|:---|
| **`menu_name`** | Tên menu | Dịch ngắn gọn (1-3 từ), sử dụng thuật ngữ website đại học chuẩn (ví dụ: 'Giới thiệu' -> 'About', 'Đào tạo' -> 'Academics'). |
| **`category_name`** | Tên danh mục | Dịch ngắn gọn, trang trọng phục vụ danh mục tin tức/bài viết. |
| **`short_description`**| Mô tả ngắn | Văn phong trang trọng, trôi chảy, tự nhiên và giữ đúng nghĩa gốc. |
| **`department_name`** | Tên bộ môn/khoa | Sử dụng thuật ngữ học thuật đại học chuẩn, không dịch theo nghĩa đen (ví dụ: 'Bộ môn Khoa học Máy tính' -> 'Department of Computer Science'). |
| **`department_description`**| Mô tả bộ môn | Văn phong học thuật, trang trọng giới thiệu khoa/bộ môn. |
| **`position_name`** | Tên chức vụ | Chức danh giảng viên/nhân sự đại học chuẩn tiếng Anh (ví dụ: 'Trưởng bộ môn' -> 'Head of Department', 'Giảng viên' -> 'Lecturer'). |
| **`position_description`**| Mô tả chức vụ | Mô tả nhiệm vụ rõ ràng, trang trọng, văn phong nhân sự/hành chính. |
| **`english_name`** | Tên tiếng Anh | Tối ưu hóa chuyển ngữ chính xác cho các trường tên riêng học thuật/thực thể. |
| **`research_direction`**| Hướng nghiên cứu | Dịch chính xác thuật ngữ chuyên ngành khoa học, kỹ thuật và học thuật (ví dụ: 'Học máy' -> 'Machine Learning'). |
| **`article_title`** | Tiêu đề bài viết | Viết hoa các từ chính (Title Case) đối với tiếng Anh, văn phong báo chí trang trọng. |
| **`article_summary`**| Tóm tắt bài viết | Văn phong tin tức, trôi chảy, tự nhiên. |
| **`scientific_profile`**| Lý lịch khoa học (HTML) | Dịch thuật ngữ học thuật, chức danh giảng viên, tên các bài báo/đề tài. Bảo toàn 100% cấu trúc HTML. |
| **`article_content`** | Nội dung bài viết (HTML) | Văn phong báo chí, tin tức đại học trang trọng. Bảo toàn 100% cấu trúc HTML, thuộc tính, class, href, src. |

---

## 2. Bản đồ tích hợp Context theo Module CMS

Dưới đây là bảng hướng dẫn chi tiết các màn hình Admin và trường dữ liệu tương ứng cần truyền `context`:

### Module 1: Quản lý Menu (`Menu Management`)
- **API sử dụng**: `/api/v1/translation` hoặc `/api/v1/translation/batch`
- **Trường dữ liệu**: Tên mục menu (`name`)
- **Mã `context`**: **`menu_name`**

### Module 2: Quản lý Danh mục (`Category Management`)
- **API sử dụng**: `/api/v1/translation` hoặc `/api/v1/translation/batch`
- **Trường dữ liệu**: Tên danh mục (`name`)
- **Mã `context`**: **`category_name`**

### Module 3: Quản lý Bài viết (`Article Management`)
- **Tiêu đề bài viết**:
  - **API**: `/api/v1/translation`
  - **Mã `context`**: **`article_title`**
- **Tóm tắt bài viết (Mô tả ngắn)**:
  - **API**: `/api/v1/translation`
  - **Mã `context`**: **`article_summary`**
- **Nội dung chi tiết bài viết (Rich Text Editor/CKEditor)**:
  - **API**: `/api/v1/translation/html`
  - **Mã `context`**: **`article_content`**

### Module 4: Quản lý Bộ môn/Khoa (`Department Management`)
- **Tên khoa/bộ môn**:
  - **API**: `/api/v1/translation`
  - **Mã `context`**: **`department_name`**
- **Mô tả khoa/bộ môn**:
  - **API**: `/api/v1/translation`
  - **Mã `context`**: **`department_description`**

### Module 5: Quản lý Chức vụ (`Position Management`)
- **Tên chức vụ**:
  - **API**: `/api/v1/translation`
  - **Mã `context`**: **`position_name`**
- **Mô tả chức vụ**:
  - **API**: `/api/v1/translation`
  - **Mã `context`**: **`position_description`**

### Module 6: Quản lý Giảng viên & Lý lịch khoa học (`Staff Management`)
- **Tên tiếng Anh / Tên quốc tế**:
  - **API**: `/api/v1/translation`
  - **Mã `context`**: **`english_name`**
- **Hướng nghiên cứu chuyên sâu**:
  - **API**: `/api/v1/translation`
  - **Mã `context`**: **`research_direction`**
- **Lý lịch khoa học / CV (CKEditor)**:
  - **API**: `/api/v1/translation/html`
  - **Mã `context`**: **`scientific_profile`**

---

## 3. Ví dụ về Payload & Response

### 3.1 API Dịch Đơn lẻ (`POST /api/v1/translation`)

**Request Payload:**
```json
{
  "text": "Trưởng bộ môn",
  "target_languages": ["en"],
  "context": "position_name"
}
```

**Response (200 OK):**
```json
{
  "vi": "Trưởng bộ môn",
  "en": "Head of Department"
}
```

### 3.2 API Dịch Batch (`POST /api/v1/translation/batch`)

**Request Payload:**
```json
{
  "texts": ["Thông báo", "Tuyển sinh"],
  "target_languages": ["en"],
  "context": "category_name"
}
```

**Response (200 OK):**
```json
[
  {
    "vi": "Thông báo",
    "en": "Announcements"
  },
  {
    "vi": "Tuyển sinh",
    "en": "Admissions"
  }
]
```

### 3.3 API Dịch HTML CKEditor (`POST /api/v1/translation/html`)

**Request Payload:**
```json
{
  "html": "<p>Vui lòng click <a href=\"/docs/intro\" target=\"_blank\">vào đây</a> để đọc thêm thông tin.</p>",
  "target_languages": ["en"],
  "context": "article_content"
}
```

**Response (200 OK):**
```json
{
  "vi": "<p>Vui lòng click <a href=\"/docs/intro\" target=\"_blank\">vào đây</a> để đọc thêm thông tin.</p>",
  "en": "<p>Please click <a href=\"/docs/intro\" target=\"_blank\">here</a> to read more information.</p>"
}
```

### 3.4 Trường hợp gửi sai Context Code

**Request Payload:**
```json
{
  "text": "Khoa học Máy tính",
  "target_languages": ["en"],
  "context": "invalid_context_code"
}
```

**Response (422 Unprocessable Entity):**
```json
{
  "detail": [
    {
      "type": "enum",
      "loc": ["body", "context"],
      "msg": "Input should be 'menu_name', 'category_name', 'short_description', 'department_name', 'department_description', 'position_name', 'position_description', 'english_name', 'research_direction', 'article_title', 'article_summary', 'scientific_profile' or 'article_content'",
      "input": "invalid_context_code",
      "ctx": {
        "expected": "'menu_name', 'category_name', 'short_description', 'department_name', 'department_description', 'position_name', 'position_description', 'english_name', 'research_direction', 'article_title', 'article_summary', 'scientific_profile' or 'article_content'"
      }
    }
  ]
}
```

---

## 4. Các Quy tắc quan trọng dành cho FE

1. **Tính tương thích ngược**: Nếu FE không truyền trường `context` (hoặc gửi `null`), API vẫn hoạt động bình thường bằng cách sử dụng prompt mặc định chung của hệ thống.
2. **Kiểm tra kỹ mã Enum**: Phải đảm bảo truyền đúng mã Enum dưới dạng chữ thường (`snake_case`) giống như bảng danh sách ở mục 1. Mọi giá trị khác sẽ bị Backend chặn lại ngay tại tầng Validation (HTTP 422).
3. **Phân biệt HTML và Text thường**: 
   - `scientific_profile` và `article_content` chỉ được dùng cho API `/api/v1/translation/html`.
   - Các context còn lại dùng cho API `/api/v1/translation` hoặc `/api/v1/translation/batch`.
