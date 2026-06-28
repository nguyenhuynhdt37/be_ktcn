# Roles and Permissions Management API

> Tài liệu hướng dẫn tích hợp hệ thống quản lý Vai trò (Roles) và Quyền hạn (Permissions) dành cho **Frontend Developer**.  
> Base URL: `http://localhost:8000/api/v1`  
> Yêu cầu header xác thực: `Authorization: Bearer <access_token>`.

---

## 1. Tổng quan thiết kế & Phân quyền

### Quy định chung
Hệ thống sử dụng mô hình bảo mật RBAC (Role-Based Access Control):
- **Vai trò (Role)**: Nhóm các quyền hạn hệ thống (ví dụ: `editor`, `author`). Mỗi vai trò liên kết với nhiều quyền hạn.
- **Quyền hạn (Permission)**: Các thao tác nghiệp vụ cụ thể (ví dụ: `article.create`, `user.view`).
- **Khóa bảo vệ vai trò (System & Super Admin Protection)**:
  - Vai trò `super_admin` là vai trò tối cao của hệ thống. Hệ thống **chặn mọi hành động** sửa tên, xóa, hoặc thay đổi quyền hạn được gán của vai trò `super_admin` từ API. Nếu thực hiện sẽ trả về mã lỗi `SUPERADMIN_ROLE_PROTECTED` (HTTP 400).
  - Tài khoản có vai trò `super_admin` tự động được cấp toàn bộ quyền mà không cần gán thủ công qua bảng liên kết.
  - **4 vai trò hệ thống cố định** (`super_admin`, `admin`, `editor`, `author`) **không thể bị xóa** khỏi hệ thống. Nếu cố tình xóa sẽ trả về mã lỗi `SYSTEM_ROLE_PROTECTED` (HTTP 400).

### Bảng phân quyền gọi API

| API Endpoints | Hành động | Quyền hạn yêu cầu |
|---|---|---|
| `GET /roles` | Xem danh sách vai trò | `role.view` |
| `GET /roles/{id}` | Xem chi tiết vai trò | `role.view` |
| `POST /roles` | Tạo vai trò mới | `role.create` |
| `PUT /roles/{id}` | Cập nhật vai trò | `role.update` |
| `DELETE /roles/{id}` | Xóa vai trò | `role.delete` |
| `POST /roles/{id}/permissions` | Gán danh sách quyền cho vai trò | `role.assign_permission` |
| `GET /permissions` | Liệt kê tất cả các quyền hạn hệ thống | `permission.view` |

---

## 2. Đặc tả API Chi tiết

### 2.1. Liệt kê danh sách vai trò
Lấy danh sách tất cả các vai trò, đi kèm số lượng quyền hạn hiện tại của từng vai trò để hiển thị danh sách compact ở Frontend.

- **Request**:
  ```http
  GET /api/v1/roles
  Authorization: Bearer <access_token>
  ```

- **Response `200 OK`**:
  ```json
  [
    {
      "id": "d1017cf7-88b3-4f9e-c616-3e4b3c75ad01",
      "name": "Super Admin",
      "code": "super_admin",
      "description": "Has full access to all modules and configurations",
      "permissions_count": 82
    },
    {
      "id": "d1017cf7-88b3-4f9e-c616-3e4b3c75ad03",
      "name": "Editor",
      "code": "editor",
      "description": "Editor who can create and update content across the platform",
      "permissions_count": 24
    }
  ]
  ```

---

### 2.2. Xem chi tiết vai trò (Role Details)
Xem chi tiết một vai trò cụ thể kèm theo toàn bộ danh sách đối tượng quyền hạn chi tiết được gán cho vai trò đó.

- **Request**:
  ```http
  GET /api/v1/roles/d1017cf7-88b3-4f9e-c616-3e4b3c75ad03
  Authorization: Bearer <access_token>
  ```

- **Response `200 OK`**:
  ```json
  {
    "id": "d1017cf7-88b3-4f9e-c616-3e4b3c75ad03",
    "name": "Editor",
    "code": "editor",
    "description": "Editor who can create and update content across the platform",
    "permissions": [
      {
        "id": "ae497478-f188-513c-939f-661a36bf5a76",
        "name": "View Dashboard",
        "code": "dashboard.view",
        "module": "dashboard",
        "action": "view",
        "description": "Allow viewing administration dashboard"
      },
      {
        "id": "8bf00c5b-e2f3-535f-8e1f-43e7f04009d5",
        "name": "Create Articles",
        "code": "article.create",
        "module": "article",
        "action": "create",
        "description": "Allow creating new articles"
      }
    ]
  }
  ```

---

### 2.3. Tạo vai trò mới
Tạo một vai trò mới. Mã định danh `code` phải là duy nhất và viết thường không dấu (ví dụ: `content_reviewer`).

- **Request**:
  ```http
  POST /api/v1/roles
  Content-Type: application/json
  Authorization: Bearer <access_token>
  ```
  ```json
  {
    "name": "Kiểm duyệt nội dung",
    "code": "content_reviewer",
    "description": "Dành cho nhân sự duyệt bài viết trước khi xuất bản"
  }
  ```

- **Response `200 OK`**:
  ```json
  {
    "id": "e95ff30e-c305-5e26-9988-0f6a9a3d65ed",
    "name": "Kiểm duyệt nội dung",
    "code": "content_reviewer",
    "description": "Dành cho nhân sự duyệt bài viết trước khi xuất bản",
    "permissions": []
  }
  ```

---

### 2.4. Cập nhật vai trò
Cập nhật tên và mô tả của vai trò.  
⚠️ *Lưu ý*: Không cho phép sửa đổi vai trò `super_admin`.

- **Request**:
  ```http
  PUT /api/v1/roles/e95ff30e-c305-5e26-9988-0f6a9a3d65ed
  Content-Type: application/json
  Authorization: Bearer <access_token>
  ```
  ```json
  {
    "name": "Ban kiểm duyệt nội dung",
    "description": "Cập nhật mô tả mới cho ban duyệt bài viết"
  }
  ```

- **Response `200 OK`**:
  ```json
  {
    "id": "e95ff30e-c305-5e26-9988-0f6a9a3d65ed",
    "name": "Ban kiểm duyệt nội dung",
    "code": "content_reviewer",
    "description": "Cập nhật mô tả mới cho ban duyệt bài viết",
    "permissions": []
  }
  ```

---

### 2.5. Xóa vai trò
Xóa vai trò khỏi hệ thống.  
⚠️ *Lưu ý*: Không cho phép xóa vai trò `super_admin`.

- **Request**:
  ```http
  DELETE /api/v1/roles/e95ff30e-c305-5e26-9988-0f6a9a3d65ed
  Authorization: Bearer <access_token>
  ```

- **Response `200 OK`**:
  ```json
  {
    "success": true
  }
  ```

---

### 2.6. Gán danh sách quyền hạn cho Vai trò (Assign Permissions)
Cập nhật lại toàn bộ danh sách quyền hạn liên kết với vai trò đó. Truyền vào danh sách dạng mảng chứa các `id` của quyền hạn.  
⚠️ *Lưu ý*: Không cho phép thay đổi quyền hạn của vai trò `super_admin`.

- **Request**:
  ```http
  POST /api/v1/roles/e95ff30e-c305-5e26-9988-0f6a9a3d65ed/permissions
  Content-Type: application/json
  Authorization: Bearer <access_token>
  ```
  ```json
  {
    "permission_ids": [
      "ae497478-f188-513c-939f-661a36bf5a76",
      "8bf00c5b-e2f3-535f-8e1f-43e7f04009d5"
    ]
  }
  ```

- **Response `200 OK`**:
  ```json
  {
    "success": true
  }
  ```

---

### 2.7. Liệt kê tất cả các quyền hạn hệ thống
Dùng để Frontend tải về toàn bộ danh sách quyền hạn có sẵn trên hệ thống, phân chia nhóm theo cột `module` để vẽ giao diện check list phân quyền cho vai trò.

- **Request**:
  ```http
  GET /api/v1/permissions
  Authorization: Bearer <access_token>
  ```

- **Response `200 OK`**:
  ```json
  [
    {
      "id": "ae497478-f188-513c-939f-661a36bf5a76",
      "name": "View Dashboard",
      "code": "dashboard.view",
      "module": "dashboard",
      "action": "view",
      "description": "Allow viewing administration dashboard"
    },
    {
      "id": "8bf00c5b-e2f3-535f-8e1f-43e7f04009d5",
      "name": "Create Articles",
      "code": "article.create",
      "module": "article",
      "action": "create",
      "description": "Allow creating new articles"
    }
  ]
  ```

---

## 3. Danh sách Mã lỗi & Xử lý (Error Codes)

| HTTP Status | error_code | Ý nghĩa |
|---|---|---|
| `400` | `SUPERADMIN_ROLE_PROTECTED` | Cố gắng chỉnh sửa, xóa hoặc thay đổi quyền hạn của vai trò Super Admin |
| `400` | `SYSTEM_ROLE_PROTECTED` | Cố gắng xóa các vai trò hệ thống cố định (`super_admin`, `admin`, `editor`, `author`) |
| `400` | `ROLE_HAS_ASSIGNED_USERS` | Cố gắng xóa vai trò đang được gán cho người dùng (bắt buộc chuyển vai trò của họ trước) |
| `400` | `INVALID_PERMISSIONS_PROVIDED` | Danh sách ID quyền hạn gửi lên chứa ID không hợp lệ trong hệ thống |
| `403` | `FORBIDDEN_ACCESS` | Tài khoản hiện tại không có đủ quyền gọi API quản trị |
| `404` | `ROLE_NOT_FOUND` | Không tìm thấy vai trò với ID yêu cầu |
| `409` | `ROLE_CODE_DUPLICATE` | Tạo vai trò mới với `code` đã tồn tại trong hệ thống |

---

## 4. Hướng dẫn tích hợp Frontend (TypeScript)

### 4.1. Interfaces mô tả kiểu dữ liệu

```typescript
export interface SystemPermission {
  id: string
  name: string
  code: string
  module: string
  action: string
  description: string | null
}

export interface RoleListItem {
  id: string
  name: string
  code: string
  description: string | null
  permissions_count: number
}

export interface RoleDetail {
  id: string
  name: string
  code: string
  description: string | null
  permissions: SystemPermission[]
}

export interface RoleCreatePayload {
  name: string
  code: string
  description?: string
}

export interface RoleUpdatePayload {
  name: string
  description?: string
}

export interface AssignPermissionsPayload {
  permission_ids: string[]
}
```

### 4.2. API Service mẫu

```typescript
import { httpClient } from '@/services/http/client'
import type { 
  RoleListItem, 
  RoleDetail, 
  RoleCreatePayload, 
  RoleUpdatePayload, 
  SystemPermission,
  AssignPermissionsPayload
} from './types'

export const rolesApi = {
  // Lấy danh sách vai trò
  list: () => 
    httpClient.get<RoleListItem[]>('/roles'),

  // Xem chi tiết vai trò
  getDetail: (id: string) => 
    httpClient.get<RoleDetail>(`/roles/${id}`),

  // Tạo vai trò
  create: (payload: RoleCreatePayload) => 
    httpClient.post<RoleDetail>('/roles', payload),

  // Cập nhật tên/mô tả vai trò
  update: (id: string, payload: RoleUpdatePayload) => 
    httpClient.put<RoleDetail>(`/roles/${id}`, payload),

  // Xóa vai trò
  delete: (id: string) => 
    httpClient.delete<{ success: boolean }>(`/roles/${id}`),

  // Gán quyền cho vai trò
  assignPermissions: (roleId: string, permissionIds: string[]) => 
    httpClient.post<{ success: boolean }>(`/roles/${roleId}/permissions`, {
      permission_ids: permissionIds
    } as AssignPermissionsPayload),

  // Lấy tất cả quyền hạn có trong hệ thống
  listAllPermissions: () => 
    httpClient.get<SystemPermission[]>('/permissions'),
}
```

### 4.3. Gợi ý cấu trúc UI cho chức năng phân quyền (Role Manager)

```
[Trang Quản lý Vai trò]
  ├── Cột bên trái: Danh sách Role Cards (Compact list)
  │     Hiển thị: Tên vai trò, Mã code, Số lượng quyền gán (ví dụ: "24 quyền hạn")
  │     Nút: "Thêm vai trò mới" ở đầu.
  │
  └── Cột bên phải: Chi tiết Vai trò & Bảng phân quyền
        Khi click chọn 1 Role ở cột trái, cột phải tải dữ liệu chi tiết:
        1. Form Sửa nhanh: Tên vai trò, Mô tả (Nút "Lưu thông tin").
        2. Phần Phân Quyền (Grid các Module):
             Nhóm danh sách `permissions` nhận từ `/permissions` theo cột `module`.
             Vẽ mỗi `module` thành 1 Box/Card:
               - Header Box: Checkbox "Chọn tất cả" + Tên Module (ví dụ: "Bài viết (article)")
               - Body Box: Grid các Checkbox con tương ứng với từng Permission action:
                   [ ] Xem bài viết          [ ] Tạo bài viết
                   [ ] Chỉnh sửa bài viết    [ ] Xóa bài viết
        3. Nút hành động cuối trang:
             - Nút "Cập nhật phân quyền" (gọi API `/roles/{id}/permissions` với danh sách checkbox đang tích).
             - Nút "Xóa vai trò này" (màu đỏ, ẩn đi nếu vai trò là `super_admin`).
```

### 4.4. Cách nhóm danh sách Permission theo Module trên Frontend

```typescript
// Tiện ích hỗ trợ nhóm permissions theo module để vẽ giao diện grid checkbox
export function groupPermissionsByModule(permissions: SystemPermission[]): Record<string, SystemPermission[]> {
  return permissions.reduce((acc, perm) => {
    const module = perm.module
    if (!acc[module]) acc[module] = []
    acc[module].push(perm)
    return acc
  }, {} as Record<string, SystemPermission[]>)
}

// Ví dụ kết quả sau nhóm:
// {
//   article: [ { id: "...", name: "View", code: "article.view", ... }, { ... } ],
//   user: [ { id: "...", name: "Create", code: "user.create", ... } ],
// }
```

### 4.5. Tích hợp React + TanStack Query & Quản lý State Checkbox

Dưới đây là mã nguồn mẫu React Hooks sử dụng `@tanstack/react-query` và `Axios` để quản lý giao diện phân quyền vai trò:

```tsx
import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { rolesApi } from './api';
import { groupPermissionsByModule } from './utils';

interface RolePermissionEditorProps {
  roleId: string;
}

export const RolePermissionEditor: React.FC<RolePermissionEditorProps> = ({ roleId }) => {
  const queryClient = useQueryClient();

  // 1. Tải tất cả quyền hạn có sẵn trên hệ thống
  const { data: allPermissions = [] } = useQuery({
    queryKey: ['permissions'],
    queryFn: async () => {
      const res = await rolesApi.listAllPermissions();
      return res.data;
    },
  });

  // 2. Tải chi tiết vai trò cùng các quyền hạn đã gán hiện tại
  const { data: roleDetail } = useQuery({
    queryKey: ['roles', roleId],
    queryFn: async () => {
      const res = await rolesApi.getDetail(roleId);
      return res.data;
    },
    enabled: !!roleId,
  });

  // State lưu trữ các ID quyền hạn đang được chọn trên giao diện
  const [selectedPermissionIds, setSelectedPermissionIds] = useState<string[]>([]);

  // Đồng bộ hóa trạng thái checkbox khi tải dữ liệu vai trò thành công
  useEffect(() => {
    if (roleDetail?.permissions) {
      setSelectedPermissionIds(roleDetail.permissions.map((p) => p.id));
    }
  }, [roleDetail]);

  // Mutation cập nhật quyền hạn lên Backend
  const assignMutation = useMutation({
    mutationFn: (permissionIds: string[]) => rolesApi.assignPermissions(roleId, permissionIds),
    onSuccess: () => {
      // Làm mới dữ liệu vai trò để hiển thị thông tin mới nhất
      queryClient.invalidateQueries({ queryKey: ['roles', roleId] });
      queryClient.invalidateQueries({ queryKey: ['roles'] }); // Reload list để cập nhật count
      alert('Cập nhật quyền hạn vai trò thành công!');
    },
    onError: (err: any) => {
      const errMsg = err?.response?.data?.error?.message || 'Có lỗi xảy ra';
      alert(`Lỗi: ${errMsg}`);
    },
  });

  // Toggle chọn từng quyền hạn riêng lẻ
  const handleTogglePermission = (permissionId: string) => {
    setSelectedPermissionIds((prev) =>
      prev.includes(permissionId)
        ? prev.filter((id) => id !== permissionId)
        : [...prev, permissionId]
    );
  };

  // Toggle "Chọn tất cả" quyền hạn thuộc một Module cụ thể
  const handleToggleModule = (moduleName: string, modulePermissions: any[]) => {
    const moduleIds = modulePermissions.map((p) => p.id);
    const hasAll = moduleIds.every((id) => selectedPermissionIds.includes(id));

    if (hasAll) {
      // Nếu đã chọn tất cả thuộc module -> bỏ chọn toàn bộ module
      setSelectedPermissionIds((prev) => prev.filter((id) => !moduleIds.includes(id)));
    } else {
      // Nếu chưa chọn hết -> tích chọn tất cả các quyền thuộc module đó
      setSelectedPermissionIds((prev) => {
        const otherIds = prev.filter((id) => !moduleIds.includes(id));
        return [...otherIds, ...moduleIds];
      });
    }
  };

  // Nhóm permissions theo module
  const permissionsByModule = groupPermissionsByModule(allPermissions);

  return (
    <div className="p-6 bg-white rounded-lg shadow-sm">
      <h2 className="text-xl font-bold mb-4">Phân quyền vai trò: {roleDetail?.name}</h2>
      
      {/* Danh sách các Module dưới dạng Cards */}
      <div className="space-y-6">
        {Object.entries(permissionsByModule).map(([moduleName, perms]) => {
          const moduleIds = perms.map((p) => p.id);
          const isAllModuleChecked = moduleIds.every((id) => selectedPermissionIds.includes(id));

          return (
            <div key={moduleName} className="border rounded-lg p-4 bg-gray-50">
              {/* Header Module Card */}
              <div className="flex items-center justify-between border-b pb-2 mb-3">
                <span className="font-semibold capitalize text-gray-800">{moduleName}</span>
                <label className="flex items-center space-x-2 text-sm cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={isAllModuleChecked}
                    onChange={() => handleToggleModule(moduleName, perms)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span>Chọn tất cả</span>
                </label>
              </div>

              {/* Grid Permission Checkboxes */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {perms.map((perm) => (
                  <label key={perm.id} className="flex items-start space-x-2 text-sm cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={selectedPermissionIds.includes(perm.id)}
                      onChange={() => handleTogglePermission(perm.id)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 mt-0.5"
                    />
                    <div>
                      <div className="font-medium text-gray-700">{perm.name}</div>
                      <div className="text-xs text-gray-400">{perm.code}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Nút hành động */}
      <div className="mt-6 flex justify-end space-x-3">
        <button
          onClick={() => setSelectedPermissionIds(roleDetail?.permissions.map((p) => p.id) || [])}
          className="px-4 py-2 border rounded-md text-sm text-gray-600 hover:bg-gray-50"
        >
          Khôi phục ban đầu
        </button>
        <button
          onClick={() => assignMutation.mutate(selectedPermissionIds)}
          disabled={assignMutation.isPending}
          className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 disabled:opacity-50"
        >
          {assignMutation.isPending ? 'Đang lưu...' : 'Lưu quyền hạn'}
        </button>
      </div>
    </div>
  );
};
```

---

## 5. Danh sách kiểm tra UX chuẩn chỉ (UX Checklist cho FE)
* [ ] **Trạng thái disable cho Super Admin**: Đối với vai trò `super_admin`, vô hiệu hóa (disabled) toàn bộ checkbox phân quyền, vì vai trò này luôn có toàn quyền hệ thống mặc định từ Backend (tránh việc người dùng sửa đổi làm lỗi nghiệp vụ).
* [ ] **Ẩn nút Xóa/Sửa**: Ẩn nút "Xóa vai trò" và khóa trường "Mã vai trò (code)" của vai trò `super_admin`. Ngoài ra, cũng ẩn nút "Xóa vai trò" đối với 3 vai trò hệ thống cố định khác (`admin`, `editor`, `author`).
* [ ] **Xử lý cảnh báo vai trò đang sử dụng**: Khi nhấn "Xóa vai trò" và nhận mã lỗi `ROLE_HAS_ASSIGNED_USERS` từ Backend, hãy hiển thị hộp thoại thông báo chi tiết (ví dụ: "Không thể xóa vai trò này vì đang có N người dùng sử dụng. Hãy thay đổi vai trò của những người này trước").
* [ ] **Trạng thái Loading và Empty**: Hiển thị xương (Skeleton loaders) khi đang tải danh sách vai trò hoặc danh sách quyền hạn.
* [ ] **Feedback thông báo rõ ràng**: Khi lưu thành công, hiển thị Toast thông báo thành công hoặc lỗi với `error_code` tương ứng nếu có.

---

*Tài liệu tạo tự động — cập nhật lần cuối: 2026-06-27*

