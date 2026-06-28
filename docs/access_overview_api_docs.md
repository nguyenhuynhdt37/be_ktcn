# Access Overview API

> Tài liệu dành cho **Frontend Developer**.  
> Base URL: `http://localhost:8000/api/v1`  
> Tất cả endpoint đều yêu cầu `Authorization: Bearer <access_token>`.

---

## Mục lục

1. [Tổng quan chức năng](#1-tổng-quan-chức-năng)
2. [GET /users/{id}/access-overview](#2-get-usersidaccess-overview)
3. [Cấu trúc dữ liệu đầy đủ](#3-cấu-trúc-dữ-liệu-đầy-đủ)
4. [Cấu trúc lỗi chung](#4-cấu-trúc-lỗi-chung)
5. [Hướng dẫn tích hợp FE](#5-hướng-dẫn-tích-hợp-fe)

---

## 1. Tổng quan chức năng

Endpoint này trả về **tổng quan toàn bộ quyền truy cập** của một tài khoản, bao gồm:

- **Roles** → danh sách vai trò được gán cho tài khoản
- **Permission codes** → tất cả mã quyền được cấp (tổng hợp từ tất cả roles)
- **Accessible features** → các tính năng/mục menu mà tài khoản có thể truy cập, **kèm danh sách quyền cụ thể** được cấp cho từng tính năng đó

### ⚠️ Chỉ dành cho Super Admin

Endpoint này **chỉ cho phép tài khoản `super_admin` gọi**. Tài khoản khác nhận `403 SUPERADMIN_REQUIRED`.

### Logic phân quyền

```
User → Roles → Permissions (M:N)
Feature → Permissions (M:N via feature_permissions)

accessible_features = [
  feature
  for feature in all_features
  if feature.permissions ∩ user.granted_permissions ≠ ∅
]
```

Mỗi feature trong kết quả chỉ liệt kê các quyền mà người dùng **thực sự được cấp** (intersection), không phải toàn bộ quyền của feature.

---

## 2. GET /users/{id}/access-overview

### Request

```http
GET /api/v1/users/{user_id}/access-overview
Authorization: Bearer <access_token>
```

| Tham số | Vị trí | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|---|
| `user_id` | path | UUID | ✅ | ID của người dùng cần xem |

### Response `200 OK`

```json
{
  "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "username": "john_editor",
  "full_name": "John Editor",
  "is_active": true,
  "roles": [
    {
      "id": "d1017cf7-88b3-4f9e-c616-3e4b3c75ad03",
      "name": "Editor",
      "code": "editor"
    }
  ],
  "permission_codes": [
    "article.create",
    "article.update",
    "article.view",
    "article.view_own",
    "category.view",
    "dashboard.view",
    "media.upload",
    "media.view_own",
    "profile.change_password",
    "profile.update",
    "profile.view"
  ],
  "accessible_features": [
    {
      "id": "f1017cf7-88b3-4f9e-c616-3e4b3c75af01",
      "name": "Dashboard",
      "code": "dashboard",
      "route": "/dashboard",
      "icon": "dashboard-icon",
      "sort_order": 1,
      "is_visible": true,
      "granted_permissions": [
        {
          "id": "ae497478-f188-513c-939f-661a36bf5a76",
          "name": "View Dashboard",
          "code": "dashboard.view",
          "module": "dashboard",
          "action": "view",
          "description": "Allow viewing administration dashboard"
        }
      ]
    },
    {
      "id": "f1017cf7-88b3-4f9e-c616-3e4b3c75af02",
      "name": "Articles",
      "code": "articles",
      "route": "/articles",
      "icon": "article-icon",
      "sort_order": 2,
      "is_visible": true,
      "granted_permissions": [
        {
          "id": "92ec922a-df7b-5c8f-92ac-8ae3749126c6",
          "name": "View All Articles",
          "code": "article.view",
          "module": "article",
          "action": "view",
          "description": "Allow viewing all articles"
        },
        {
          "id": "8bf00c5b-e2f3-535f-8e1f-43e7f04009d5",
          "name": "Create Articles",
          "code": "article.create",
          "module": "article",
          "action": "create",
          "description": "Allow creating new articles"
        },
        {
          "id": "83055417-e999-514a-84e5-7c603b7f9500",
          "name": "Update All Articles",
          "code": "article.update",
          "module": "article",
          "action": "update",
          "description": "Allow modifying any article"
        }
      ]
    }
  ],
  "total_permissions": 11,
  "total_accessible_features": 5
}
```

### Mô tả các trường

#### Root level

| Trường | Kiểu | Mô tả |
|---|---|---|
| `user_id` | UUID | ID của tài khoản |
| `username` | string | Tên đăng nhập |
| `full_name` | string | Tên đầy đủ |
| `is_active` | boolean | Trạng thái tài khoản |
| `roles` | array | Danh sách vai trò được gán |
| `permission_codes` | string[] | Tất cả mã quyền được cấp (đã sắp xếp alphabet) |
| `accessible_features` | array | Các tính năng có thể truy cập |
| `total_permissions` | integer | `len(permission_codes)` |
| `total_accessible_features` | integer | `len(accessible_features)` |

#### `roles[]`

| Trường | Kiểu | Mô tả |
|---|---|---|
| `id` | UUID | ID role |
| `name` | string | Tên vai trò |
| `code` | string | Mã vai trò (vd: `editor`, `admin`) |

#### `accessible_features[]`

| Trường | Kiểu | Mô tả |
|---|---|---|
| `id` | UUID | ID tính năng |
| `name` | string | Tên tính năng hiển thị |
| `code` | string | Mã định danh tính năng |
| `route` | string \| null | Đường dẫn frontend (vd: `/articles`) |
| `icon` | string \| null | Mã icon |
| `sort_order` | integer | Thứ tự hiển thị |
| `is_visible` | boolean | Có hiển thị trên menu không |
| `granted_permissions` | array | Quyền được cấp cho tính năng này |

#### `accessible_features[].granted_permissions[]`

| Trường | Kiểu | Mô tả |
|---|---|---|
| `id` | UUID | ID quyền |
| `name` | string | Tên quyền |
| `code` | string | Mã quyền (vd: `article.create`) |
| `module` | string | Module (vd: `article`, `user`) |
| `action` | string | Hành động (vd: `view`, `create`, `update`) |
| `description` | string \| null | Mô tả quyền |

### Response lỗi

| HTTP | error_code | Nguyên nhân |
|---|---|---|
| `401` | `UNAUTHORIZED` | Thiếu hoặc token không hợp lệ |
| `403` | `SUPERADMIN_REQUIRED` | Không phải super_admin |
| `404` | `USER_NOT_FOUND` | Người dùng không tồn tại |

---

## 3. Cấu trúc dữ liệu đầy đủ

### TypeScript Interfaces

```typescript
// src/features/users/types/accessOverview.ts

export interface RoleItem {
  id: string
  name: string
  code: string
}

export interface GrantedPermission {
  id: string
  name: string
  code: string
  module: string
  action: string
  description: string | null
}

export interface AccessibleFeature {
  id: string
  name: string
  code: string
  route: string | null
  icon: string | null
  sort_order: number
  is_visible: boolean
  granted_permissions: GrantedPermission[]
}

export interface UserAccessOverview {
  user_id: string
  username: string
  full_name: string
  is_active: boolean
  roles: RoleItem[]
  permission_codes: string[]
  accessible_features: AccessibleFeature[]
  total_permissions: number
  total_accessible_features: number
}
```

---

## 4. Cấu trúc lỗi chung

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Mô tả lỗi bằng tiếng Việt",
    "details": {}
  }
}
```

| HTTP | error_code | Ý nghĩa |
|---|---|---|
| `401` | `UNAUTHORIZED` | Không có token hoặc token hết hạn |
| `403` | `SUPERADMIN_REQUIRED` | Chỉ super_admin mới được gọi endpoint này |
| `404` | `USER_NOT_FOUND` | Người dùng không tồn tại |

---

## 5. Hướng dẫn tích hợp FE

### API service

```typescript
// src/features/users/services/userAccessService.ts
import { httpClient } from '@/services/http/client'
import type { UserAccessOverview } from '../types/accessOverview'

export const userAccessService = {
  getAccessOverview: async (userId: string): Promise<UserAccessOverview> => {
    const { data } = await httpClient.get<UserAccessOverview>(
      `/users/${userId}/access-overview`
    )
    return data
  },
}
```

### TanStack Query hook

```typescript
// src/features/users/hooks/useUserAccessOverview.ts
import { useQuery } from '@tanstack/react-query'
import { userAccessService } from '../services/userAccessService'

export function useUserAccessOverview(userId: string) {
  return useQuery({
    queryKey: ['users', userId, 'access-overview'],
    queryFn: () => userAccessService.getAccessOverview(userId),
    enabled: !!userId,
    staleTime: 30_000, // cache 30 giây
  })
}
```

### Gợi ý UI cho trang UserActivityPage

```
[UserActivityPage] — /users/:id/activity
  │
  ├── Header: Avatar + Tên + Role badges + trạng thái (Active/Locked)
  │
  ├── Stat cards:
  │     "X vai trò" | "X quyền" | "X tính năng"
  │
  ├── Section: Tính năng có thể truy cập
  │     Dạng grid cards, mỗi card là 1 feature:
  │       - Icon + Tên feature
  │       - Route badge (e.g. /articles)
  │       - Danh sách Permission badges (action: view, create, update...)
  │             Màu badge theo action:
  │               view       → blue
  │               create     → green
  │               update     → yellow
  │               delete     → red
  │               publish    → purple
  │               force_delete → dark red
  │
  └── Section: Tất cả permission codes
        Dạng tag cloud hoặc danh sách compact
        Nhóm theo module (article.*, user.*, role.*, ...)
```

### Component mẫu: PermissionBadge

```tsx
// src/features/users/components/PermissionBadge.tsx
const ACTION_COLORS: Record<string, string> = {
  view:         'bg-blue-100 text-blue-700',
  view_own:     'bg-sky-100 text-sky-700',
  create:       'bg-green-100 text-green-700',
  update:       'bg-yellow-100 text-yellow-700',
  update_own:   'bg-amber-100 text-amber-700',
  delete:       'bg-red-100 text-red-700',
  delete_own:   'bg-rose-100 text-rose-700',
  publish:      'bg-purple-100 text-purple-700',
  unpublish:    'bg-violet-100 text-violet-700',
  force_delete: 'bg-red-900 text-red-100',
  upload:       'bg-teal-100 text-teal-700',
  download:     'bg-cyan-100 text-cyan-700',
  lock:         'bg-orange-100 text-orange-700',
  unlock:       'bg-lime-100 text-lime-700',
  assign_role:  'bg-indigo-100 text-indigo-700',
}

interface Props {
  code: string
  action: string
}

export function PermissionBadge({ code, action }: Props) {
  const colorClass = ACTION_COLORS[action] ?? 'bg-gray-100 text-gray-600'
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${colorClass}`}>
      {action}
    </span>
  )
}
```

### Nhóm permission_codes theo module

```typescript
// Tiện ích: nhóm danh sách permission_codes theo module
function groupPermissionsByModule(codes: string[]): Record<string, string[]> {
  return codes.reduce((acc, code) => {
    const [module] = code.split('.')
    if (!acc[module]) acc[module] = []
    acc[module].push(code)
    return acc
  }, {} as Record<string, string[]>)
}

// Ví dụ kết quả:
// {
//   article: ['article.create', 'article.update', 'article.view'],
//   dashboard: ['dashboard.view'],
//   profile: ['profile.change_password', 'profile.view', 'profile.update'],
// }
```

### Xử lý lỗi

```typescript
import { AxiosError } from 'axios'

function handleAccessOverviewError(error: AxiosError) {
  const code = (error.response?.data as any)?.error?.code
  switch (code) {
    case 'SUPERADMIN_REQUIRED':
      toast.error('Chỉ Super Admin mới có thể xem thông tin này')
      break
    case 'USER_NOT_FOUND':
      toast.error('Người dùng không tồn tại')
      break
    default:
      toast.error('Không thể tải thông tin quyền truy cập')
  }
}
```

---

*Tài liệu tạo tự động — cập nhật lần cuối: 2024-06-27*
