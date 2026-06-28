# Media Management Module API

> Tài liệu hướng dẫn tích hợp hệ thống quản lý tài nguyên (hình ảnh, tài liệu, video, PDF...) dành cho **Frontend Developer**.  
> Base URL: `http://localhost:8000/api/v1/media`  
> Yêu cầu header xác thực: `Authorization: Bearer <access_token>`.

---

## 1. Tổng quan thiết kế & Phân quyền

### Cơ chế lưu trữ
Hệ thống sử dụng **MinIO** (S3-compatible) kết hợp với **PostgreSQL**:
- **MinIO**: Lưu trữ file vật lý thực tế dưới dạng khóa phẳng (flat object key) sử dụng UUID (ví dụ: `files/3fa85f6457174562b3fc2c963f66afa6`). Điều này giúp cho việc di chuyển (`move`) và đổi tên (`rename`) diễn ra tức thời chỉ bằng 1 câu lệnh cập nhật cơ sở dữ liệu.
- **Database (PostgreSQL)**: Quản lý cây thư mục ảo, liên kết `parent_id` và các siêu dữ liệu (metadata) như tên hiển thị, dung lượng, định dạng, kích thước ảnh, MD5 checksum.
- **Thumbnail**: Đối với hình ảnh (JPEG, PNG, WEBP), hệ thống tự động sinh ảnh thu nhỏ (kích thước tối đa 200px) lưu tại MinIO khóa `thumbs/<uuid>` và trả về qua trường `thumbnail_key`.

### Bảng phân quyền RBAC

| API Endpoints | Action | Quyền yêu cầu |
|---|---|---|
| `GET /media` | Liệt kê danh sách thư mục / tệp tin | `media.view` |
| `POST /media/folders` | Tạo thư mục mới | `media.create` |
| `POST /media/upload` | Tải tập tin lên | `media.create` |
| `GET /media/{id}/download` | Tải tập tin nhị phân về máy | `media.view` |
| `GET /media/{id}/url` | Lấy đường dẫn trực tiếp | `media.view` |
| `POST /media/{id}/rename` | Đổi tên file hoặc thư mục | `media.update` |
| `POST /media/{id}/move` | Di chuyển file/folder sang folder khác | `media.update` |
| `POST /media/{id}/copy` | Nhân bản tệp tin | `media.update` |
| `DELETE /media/{id}` | Xóa file hoặc thư mục (xóa đệ quy) | `media.delete` |
| `POST /media/presigned-upload` | Sinh presigned URL để tải lên trực tiếp | `media.create` |
| `GET /media/{id}/presigned-download` | Sinh presigned URL tải xuống bảo mật | `media.view` |

---

## 2. Đặc tả API Chi tiết

### 2.1. Liệt kê thư mục & tệp tin
Lấy danh sách các tài nguyên nằm trong thư mục cha chỉ định. Nếu không gửi `parent_id`, hệ thống tự hiểu là đang lấy ở thư mục gốc (root).

- **Request**:
  ```http
  GET /api/v1/media?parent_id=d1017cf7-88b3-4f9e-c616-3e4b3c75ad01
  Authorization: Bearer <access_token>
  ```

- **Response `200 OK`**:
  ```json
  [
    {
      "id": "e95ff30e-c305-5e26-9988-0f6a9a3d65ed",
      "name": "Tài liệu marketing",
      "is_folder": true,
      "parent_id": "d1017cf7-88b3-4f9e-c616-3e4b3c75ad01",
      "object_key": null,
      "thumbnail_key": null,
      "bucket": null,
      "mime_type": null,
      "size": null,
      "checksum": null,
      "width": null,
      "height": null,
      "created_at": "2024-06-27T08:00:00Z",
      "updated_at": "2024-06-27T08:00:00Z"
    },
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "name": "banner_tuyen_sinh.png",
      "is_folder": false,
      "parent_id": "d1017cf7-88b3-4f9e-c616-3e4b3c75ad01",
      "object_key": "files/3fa85f6457174562b3fc2c963f66afa6",
      "thumbnail_key": "thumbs/9b1deb4d3b7d4bad9bdd2b0d7b3dcb6d",
      "bucket": "university-media",
      "mime_type": "image/png",
      "size": 1048576,
      "checksum": "d41d8cd98f00b204e9800998ecf8427e",
      "width": 1920,
      "height": 1080,
      "created_at": "2024-06-27T08:15:00Z",
      "updated_at": "2024-06-27T08:15:00Z"
    }
  ]
  ```

---

### 2.2. Tạo thư mục mới
Tạo một thư mục ảo để quản lý cấu trúc cây.

- **Request**:
  ```http
  POST /api/v1/media/folders
  Content-Type: application/json
  Authorization: Bearer <access_token>
  ```
  ```json
  {
    "name": "Ảnh hoạt động ngoại khóa",
    "parent_id": null
  }
  ```

- **Response `200 OK`**:
  ```json
  {
    "id": "7a497a3e-9dd0-5874-aecd-36e3b329e74d",
    "name": "Ảnh hoạt động ngoại khóa",
    "is_folder": true,
    "parent_id": null,
    "created_at": "2024-06-27T08:20:00Z",
    "updated_at": "2024-06-27T08:20:00Z"
  }
  ```

---

### 2.3. Tải tập tin lên (Multipart Upload)
Tải tệp tin trực tiếp từ client. Hỗ trợ truyền `parent_id` trong body form để đưa vào thư mục cụ thể.

- **Request**:
  ```http
  POST /api/v1/media/upload
  Content-Type: multipart/form-data
  Authorization: Bearer <access_token>
  ```
  - **Form fields**:
    - `file`: (Tập tin nhị phân)
    - `parent_id`: `7a497a3e-9dd0-5874-aecd-36e3b329e74d` (tùy chọn)

- **Response `200 OK`**:
  ```json
  {
    "id": "e22626cb-9644-5280-8d0b-3128e224269c",
    "name": "workshop_photo.jpg",
    "is_folder": false,
    "parent_id": "7a497a3e-9dd0-5874-aecd-36e3b329e74d",
    "object_key": "files/e22626cb964452808d0b3128e224269c",
    "thumbnail_key": "thumbs/8bf00c5be2f3535f8e1f43e7f04009d5",
    "bucket": "university-media",
    "mime_type": "image/jpeg",
    "size": 256102,
    "checksum": "8e1f43e7f04009d58bf00c5be2f3535f",
    "width": 1200,
    "height": 800,
    "created_at": "2024-06-27T08:25:00Z",
    "updated_at": "2024-06-27T08:25:00Z"
  }
  ```

---

### 2.4. Tải tập tin về máy (Download File)
Trả về luồng dữ liệu nhị phân của tập tin. Trình duyệt tự động mở hộp thoại tải xuống với tên file đúng.

- **Request**:
  ```http
  GET /api/v1/media/e22626cb-9644-5280-8d0b-3128e224269c/download
  Authorization: Bearer <access_token>
  ```

- **Response `200 OK`**: (Luồng nhị phân)
  - Headers:
    - `Content-Type: image/jpeg`
    - `Content-Disposition: attachment; filename=workshop_photo.jpg`

---

### 2.5. Di chuyển tập tin / thư mục (Move)
Di chuyển tài nguyên đến thư mục cha đích.  
*Lưu ý*: Hệ thống tự động ngăn chặn việc di chuyển thư mục cha vào thư mục con của chính nó.

- **Request**:
  ```http
  POST /api/v1/media/e22626cb-9644-5280-8d0b-3128e224269c/move
  Content-Type: application/json
  Authorization: Bearer <access_token>
  ```
  ```json
  {
    "parent_id": "e95ff30e-c305-5e26-9988-0f6a9a3d65ed"
  }
  ```

- **Response `200 OK`**:
  ```json
  {
    "id": "e22626cb-9644-5280-8d0b-3128e224269c",
    "parent_id": "e95ff30e-c305-5e26-9988-0f6a9a3d65ed",
    "name": "workshop_photo.jpg",
    "is_folder": false,
    ...
  }
  ```

---

### 2.6. Sao chép tập tin (Copy)
Nhân bản tập tin (nhân bản cả file vật lý trên MinIO).

- **Request**:
  ```http
  POST /api/v1/media/e22626cb-9644-5280-8d0b-3128e224269c/copy
  Content-Type: application/json
  Authorization: Bearer <access_token>
  ```
  ```json
  {
    "dest_parent_id": "e95ff30e-c305-5e26-9988-0f6a9a3d65ed"
  }
  ```

- **Response `200 OK`**:
  ```json
  {
    "id": "8ed8964d-0b51-5ca4-9ad8-92c44346e4a8",
    "parent_id": "e95ff30e-c305-5e26-9988-0f6a9a3d65ed",
    "name": "workshop_photo.jpg",
    "is_folder": false,
    "object_key": "files/new_generated_uuid_key",
    ...
  }
  ```

---

### 2.7. Xóa tập tin / thư mục (Delete)
Xóa tài nguyên khỏi hệ thống.  
⚠️ **QUAN TRỌNG**: Xóa thư mục sẽ kích hoạt quá trình quét và xóa đệ quy toàn bộ file con nằm bên trong nó (cả trên MinIO và database). Hãy sử dụng cẩn thận!

- **Request**:
  ```http
  DELETE /api/v1/media/e22626cb-9644-5280-8d0b-3128e224269c
  Authorization: Bearer <access_token>
  ```

- **Response `200 OK`**:
  ```json
  {
    "success": true
  }
  ```

---

### 2.8. Sinh S3 Presigned URL Tải lên trực tiếp
Cho phép sinh URL có thời hạn để client (Frontend) thực hiện PUT/POST trực tiếp lên MinIO mà không cần đi qua Backend, thích hợp với các file lớn.

- **Request**:
  ```http
  POST /api/v1/media/presigned-upload?filename=video_event.mp4&content_type=video/mp4&expires_in=3600
  Authorization: Bearer <access_token>
  ```

- **Response `200 OK`**:
  ```json
  {
    "url": "http://localhost:9000/university-media",
    "fields": {
      "key": "files/54a314e8544a5193842484bb18f21f90",
      "Content-Type": "video/mp4",
      "AWSAccessKeyId": "minio_admin",
      "policy": "eyJTdGF0ZW1lbnQiOiBbeyJD...==",
      "signature": "ab0c5a1993b4b233ecb288b5..."
    },
    "expires_in": 3600
  }
  ```

- **Cách sử dụng ở Frontend**:
  Frontend thực hiện gửi FormData lên `url` chứa các key trong `fields` kèm theo file nhị phân với trường tên là `file`.

---

## 3. Danh sách Mã lỗi & Xử lý (Error Codes)

Hệ thống trả về các mã lỗi cụ thể bằng tiếng Việt để hiển thị trực tiếp lên UI:

| HTTP Status | error_code | Ý nghĩa |
|---|---|---|
| `400` | `CIRCULAR_MOVE_ERROR` | Cố gắng di chuyển thư mục cha vào chính nó hoặc thư mục con |
| `400` | `NOT_A_DIRECTORY_ERROR` | Chỉ định ID cha không phải là thư mục (không thể chứa con) |
| `400` | `DOWNLOAD_DIRECTORY_ERROR` | Cố gắng download trực tiếp cả thư mục dưới dạng file |
| `400` | `STORAGE_RETRIEVAL_ERROR` | Lỗi xảy ra khi giao tiếp với MinIO để lấy file |
| `403` | `FORBIDDEN_ACCESS` | Người dùng không có quyền thao tác (thiếu quyền RBAC tương ứng) |
| `404` | `MEDIA_NOT_FOUND` | Không tìm thấy tệp tin hoặc thư mục với ID yêu cầu |

---

## 4. Hướng dẫn tích hợp Frontend (TypeScript)

### 4.1. Interfaces mô tả kiểu dữ liệu

```typescript
export interface MediaItem {
  id: string
  name: string
  is_folder: boolean
  parent_id: string | null
  object_key: string | null
  thumbnail_key: string | null
  bucket: string | null
  mime_type: string | null
  size: number | null
  checksum: string | null
  width: number | null
  height: number | null
  created_at: string
  updated_at: string
}

export interface FolderCreatePayload {
  name: string
  parent_id: string | null
}

export interface MovePayload {
  parent_id: string | null
}

export interface CopyPayload {
  dest_parent_id: string | null
}

export interface PresignedPostData {
  url: string
  fields: Record<string, string>
  expires_in: number
}
```

### 4.2. API Service mẫu

```typescript
import { httpClient } from '@/services/http/client'
import type { MediaItem, FolderCreatePayload, MovePayload, CopyPayload, PresignedPostData } from './types'

export const mediaApi = {
  // Lấy danh sách tệp tin & thư mục
  list: (parentId: string | null = null) => 
    httpClient.get<MediaItem[]>('/media', { params: { parent_id: parentId } }),

  // Tạo thư mục
  createFolder: (payload: FolderCreatePayload) => 
    httpClient.post<MediaItem>('/media/folders', payload),

  // Đổi tên
  rename: (id: string, name: string) => 
    httpClient.post<MediaItem>(`/media/${id}/rename`, { name }),

  // Di chuyển
  move: (id: string, parentId: string | null) => 
    httpClient.post<MediaItem>(`/media/${id}/move`, { parent_id: parentId } as MovePayload),

  // Sao chép
  copy: (id: string, destParentId: string | null) => 
    httpClient.post<MediaItem>(`/media/${id}/copy`, { dest_parent_id: destParentId } as CopyPayload),

  // Tải lên tập tin thường (Multipart)
  upload: (file: File, parentId: string | null = null, onProgress?: (pct: number) => void) => {
    const formData = new FormData()
    formData.append('file', file)
    if (parentId) {
      formData.append('parent_id', parentId)
    }
    return httpClient.post<MediaItem>('/media/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(percent)
        }
      }
    })
  },

  // Xóa tài nguyên
  delete: (id: string) => 
    httpClient.delete<{ success: boolean }>(`/media/${id}`),

  // Lấy link tải xuống trực tiếp
  getDownloadUrl: (id: string) => `/api/v1/media/${id}/download`,

  // Lấy link hiển thị ảnh thu nhỏ (thumbnail) trực tiếp từ MinIO
  getThumbnailUrl: (item: MediaItem) => {
    if (!item.thumbnail_key) return null
    // Sử dụng địa chỉ MinIO từ file cấu hình hệ thống
    const minioHost = import.meta.env.VITE_MINIO_HOST || 'http://localhost:9000'
    return `${minioHost}/${item.bucket || 'university-media'}/${item.thumbnail_key}`
  },

  // Tải lên trực tiếp qua Presigned URL (đối với file dung lượng lớn)
  uploadDirectToS3: async (file: File, onProgress?: (pct: number) => void) => {
    // 1. Lấy presigned post url từ backend
    const { data: presigned } = await httpClient.post<PresignedPostData>(
      `/media/presigned-upload?filename=${encodeURIComponent(file.name)}&content_type=${file.type}`
    )

    // 2. Upload trực tiếp bằng FormData
    const formData = new FormData()
    Object.entries(presigned.fields).forEach(([key, val]) => {
      formData.append(key, val)
    })
    formData.append('file', file)

    // Gửi request lên thẳng S3 mà không có header Authorization (S3 từ chối header này trong FormData)
    const xhr = new XMLHttpRequest()
    return new Promise<string>((resolve, reject) => {
      xhr.open('POST', presigned.url, true)
      
      if (xhr.upload && onProgress) {
        xhr.upload.onprogress = (e) => {
          if (e.lengthComputable) {
            const pct = Math.round((e.loaded * 100) / e.total)
            onProgress(pct)
          }
        }
      }

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          // Lấy key được lưu trữ
          const uploadedKey = presigned.fields['key']
          resolve(uploadedKey)
        } else {
          reject(new Error('Tải tập tin lên S3 thất bại.'))
        }
      }
      xhr.onerror = () => reject(new Error('Lỗi kết nối mạng.'))
      xhr.send(formData)
    })
  }
}
```

---

*Tài liệu tạo tự động — cập nhật lần cuối: 2024-06-27*
