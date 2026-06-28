# Tài liệu Các Nâng Cấp Mới — Quản lý Vai trò & Phân quyền

Tài liệu này tổng hợp **các tính năng bảo mật mới nâng cấp** của API Vai trò & Quyền hạn cùng hướng dẫn tích hợp Frontend (React + TanStack Query).

---

## 1. Các Quy định Bảo mật & Cấm Xóa Mới
Hệ thống bổ sung 2 lớp bảo vệ nghiêm ngặt ở tầng Database:
1. **Chặn xóa 4 Vai trò Hệ thống cố định** (`super_admin`, `admin`, `editor`, `author`).
   * **HTTP Status**: `400 Bad Request`
   * **error_code**: `SYSTEM_ROLE_PROTECTED`
   * **Ý nghĩa**: Các vai trò này là cốt lõi của hệ thống, không được phép xóa dưới mọi hình thức.
2. **Chặn xóa Vai trò đang được gán cho Người dùng**:
   * **HTTP Status**: `400 Bad Request`
   * **error_code**: `ROLE_HAS_ASSIGNED_USERS`
   * **Ý nghĩa**: Nếu vai trò đang được gán cho ít nhất 1 người dùng, hệ thống sẽ chặn xóa. Phải chuyển vai trò của họ sang vai trò khác trước khi thực hiện xóa vai trò này.

---

## 2. Danh sách Mã lỗi Mới bổ sung

| HTTP Status | error_code | Ý nghĩa & Cách xử lý |
|---|---|---|
| `400` | `SYSTEM_ROLE_PROTECTED` | Chặn xóa vai trò hệ thống cố định. FE nên ẩn nút Xóa của các vai trò này trên giao diện. |
| `400` | `ROLE_HAS_ASSIGNED_USERS` | Vai trò đang được sử dụng. FE cần hiển thị thông báo yêu cầu chuyển vai trò người dùng trước khi thử lại. |

---

## 3. Mã nguồn Mẫu Tích hợp React + TanStack Query (State Checkbox)

Frontend dùng React kết hợp `@tanstack/react-query` và `Axios` để quản lý giao diện check-box phân quyền như sau:

```tsx
import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';

interface SystemPermission {
  id: string;
  name: string;
  code: string;
  module: string;
  action: string;
}

interface RoleDetail {
  id: string;
  name: string;
  code: string;
  permissions: SystemPermission[];
}

export const RolePermissionEditor: React.FC<{ roleId: string }> = ({ roleId }) => {
  const queryClient = useQueryClient();

  // 1. Lấy tất cả quyền có sẵn trong hệ thống
  const { data: allPermissions = [] } = useQuery<SystemPermission[]>({
    queryKey: ['permissions'],
    queryFn: async () => {
      const res = await axios.get('/api/v1/permissions');
      return res.data;
    },
  });

  // 2. Lấy chi tiết vai trò cùng các quyền hạn đã gán hiện tại
  const { data: roleDetail } = useQuery<RoleDetail>({
    queryKey: ['roles', roleId],
    queryFn: async () => {
      const res = await axios.get(`/api/v1/roles/${roleId}`);
      return res.data;
    },
    enabled: !!roleId,
  });

  // State quản lý danh sách ID quyền được tích chọn
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  useEffect(() => {
    if (roleDetail?.permissions) {
      setSelectedIds(roleDetail.permissions.map((p) => p.id));
    }
  }, [roleDetail]);

  // Mutation cập nhật danh sách quyền cho vai trò
  const assignMutation = useMutation({
    mutationFn: (permissionIds: string[]) =>
      axios.post(`/api/v1/roles/${roleId}/permissions`, { permission_ids: permissionIds }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roles', roleId] });
      queryClient.invalidateQueries({ queryKey: ['roles'] });
      alert('Cập nhật quyền hạn vai trò thành công!');
    },
    onError: (err: any) => {
      const errMsg = err?.response?.data?.error?.message || 'Có lỗi xảy ra';
      alert(`Lỗi: ${errMsg}`);
    },
  });

  // Toggle chọn từng quyền hạn riêng lẻ
  const handleToggle = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  // Toggle "Chọn tất cả" thuộc một Module
  const handleToggleModule = (modulePermissions: SystemPermission[]) => {
    const ids = modulePermissions.map((p) => p.id);
    const hasAll = ids.every((id) => selectedIds.includes(id));

    if (hasAll) {
      setSelectedIds((prev) => prev.filter((id) => !ids.includes(id)));
    } else {
      setSelectedIds((prev) => {
        const otherIds = prev.filter((id) => !ids.includes(id));
        return [...otherIds, ...ids];
      });
    }
  };

  return (
    <div>
      {/* Giao diện hiển thị các Cards gom nhóm theo Module */}
      {/* ... Render giao diện ... */}
    </div>
  );
};
```

---

## 4. Checklist UX dành cho Frontend Developer (Quan trọng)
* [ ] **Khóa vai trò hệ thống**: Ẩn nút "Xóa vai trò" đối với 4 vai trò cố định (`super_admin`, `admin`, `editor`, `author`). Khóa trường "Mã vai trò (code)" không cho phép người dùng sửa đổi.
* [ ] **Disable cho Super Admin**: Vô hiệu hóa (disabled) toàn bộ checkbox phân quyền của vai trò `super_admin` vì vai trò này tự động bypass mọi kiểm tra quyền hạn hệ thống.
* [ ] **Xử lý Toast Cảnh báo**: Bắt mã lỗi `ROLE_HAS_ASSIGNED_USERS` khi xóa thất bại để hiển thị Modal khuyên người dùng chuyển đổi vai trò cho các tài khoản đang sử dụng trước khi xóa.
