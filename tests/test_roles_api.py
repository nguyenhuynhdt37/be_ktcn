import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import Permission, Role, User, UserRole


@pytest.fixture(autouse=True)
async def seed_roles_and_permissions(db_session: AsyncSession):
    """
    Seeds standard roles and permissions for roles API tests.
    """
    # Standard roles (super_admin is already seeded by conftest)
    admin_role = Role(
        id=uuid.UUID("d1017cf7-88b3-4f9e-c616-3e4b3c75ad02"),
        name="Admin",
        code="admin",
        description="Admin role",
    )
    editor_role = Role(
        id=uuid.UUID("d1017cf7-88b3-4f9e-c616-3e4b3c75ad03"),
        name="Editor",
        code="editor",
        description="Editor role",
    )
    author_role = Role(
        id=uuid.UUID("d1017cf7-88b3-4f9e-c616-3e4b3c75ad04"),
        name="Author",
        code="author",
        description="Author role",
    )
    db_session.add_all([admin_role, editor_role, author_role])

    # Standard permissions needed for testing
    p1 = Permission(
        id=uuid.UUID("ae497478-f188-513c-939f-661a36bf5a76"),
        name="View Roles",
        code="role.view",
        module="role",
        action="view",
        description="Allow viewing roles",
    )
    p2 = Permission(
        id=uuid.UUID("ae497478-f188-513c-939f-661a36bf5a77"),
        name="Create Roles",
        code="role.create",
        module="role",
        action="create",
        description="Allow creating roles",
    )
    p3 = Permission(
        id=uuid.UUID("ae497478-f188-513c-939f-661a36bf5a78"),
        name="Update Roles",
        code="role.update",
        module="role",
        action="update",
        description="Allow updating roles",
    )
    p4 = Permission(
        id=uuid.UUID("ae497478-f188-513c-939f-661a36bf5a79"),
        name="Delete Roles",
        code="role.delete",
        module="role",
        action="delete",
        description="Allow deleting roles",
    )
    p5 = Permission(
        id=uuid.UUID("ae497478-f188-513c-939f-661a36bf5a80"),
        name="Assign Permissions",
        code="role.assign_permission",
        module="role",
        action="assign_permission",
        description="Allow assigning permissions",
    )
    p6 = Permission(
        id=uuid.UUID("ae497478-f188-513c-939f-661a36bf5a81"),
        name="View Permissions",
        code="permission.view",
        module="permission",
        action="view",
        description="Allow viewing permissions",
    )
    db_session.add_all([p1, p2, p3, p4, p5, p6])
    await db_session.commit()



# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _get_admin_token(client: AsyncClient) -> str:
    resp = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "adminpassword"})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ─── Role CRUD Tests ─────────────────────────────────────────────────────────

class TestRoleCRUD:
    async def test_list_roles_success(self, client: AsyncClient) -> None:
        """Kiểm tra lấy danh sách vai trò thành công."""
        token = await _get_admin_token(client)
        resp = await client.get("/api/v1/roles", headers=_auth(token))
        assert resp.status_code == 200
        roles = resp.json()
        assert len(roles) >= 4  # super_admin, admin, editor, author
        
        # Check structure
        for role in roles:
            for field in ("id", "name", "code", "permissions_count"):
                assert field in role

    async def test_get_role_detail_success(self, client: AsyncClient, db_session: AsyncSession) -> None:
        """Kiểm tra lấy chi tiết vai trò."""
        token = await _get_admin_token(client)

        # Lấy một vai trò ngẫu nhiên từ DB
        stmt = select(Role).limit(1)
        res = await db_session.execute(stmt)
        role = res.scalar_one()

        resp = await client.get(f"/api/v1/roles/{role.id}", headers=_auth(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(role.id)
        assert data["code"] == role.code
        assert "permissions" in data
        assert isinstance(data["permissions"], list)

    async def test_create_role_success(self, client: AsyncClient) -> None:
        """Kiểm tra tạo vai trò mới thành công."""
        token = await _get_admin_token(client)
        payload = {
            "name": "Nhân viên kiểm thử",
            "code": "test_qa_role",
            "description": "Role dành cho QA/QC",
        }
        resp = await client.post("/api/v1/roles", json=payload, headers=_auth(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == payload["name"]
        assert data["code"] == payload["code"]
        assert data["description"] == payload["description"]
        assert data["permissions"] == []

    async def test_create_role_duplicate_code_conflict(self, client: AsyncClient) -> None:
        """Tạo vai trò trùng mã code phải trả về 409 Conflict."""
        token = await _get_admin_token(client)
        payload = {
            "name": "Duplicate Role",
            "code": "super_admin",  # Đã tồn tại trong hạt giống
        }
        resp = await client.post("/api/v1/roles", json=payload, headers=_auth(token))
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "ROLE_CODE_DUPLICATE"

    async def test_update_role_success(self, client: AsyncClient, db_session: AsyncSession) -> None:
        """Kiểm tra cập nhật thông tin vai trò."""
        token = await _get_admin_token(client)

        # Tạo 1 role để update
        new_role = Role(name="Original Name", code="role_to_update", description="Orig")
        db_session.add(new_role)
        await db_session.commit()
        await db_session.refresh(new_role)

        payload = {
            "name": "Updated Name",
            "description": "Updated Description",
        }
        resp = await client.put(f"/api/v1/roles/{new_role.id}", json=payload, headers=_auth(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "Updated Description"

    async def test_delete_role_success(self, client: AsyncClient, db_session: AsyncSession) -> None:
        """Kiểm tra xóa vai trò thành công."""
        token = await _get_admin_token(client)

        # Tạo 1 role để xóa
        role_to_del = Role(name="Delete Me", code="role_to_delete")
        db_session.add(role_to_del)
        await db_session.commit()
        await db_session.refresh(role_to_del)

        resp = await client.delete(f"/api/v1/roles/{role_to_del.id}", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        # Verify deletion from DB
        stmt = select(Role).where(Role.id == role_to_del.id)
        res = await db_session.execute(stmt)
        assert res.scalar_one_or_none() is None


# ─── Permission Assignment & Listing Tests ────────────────────────────────────

class TestPermissionsManagement:
    async def test_list_all_permissions(self, client: AsyncClient) -> None:
        """Kiểm tra liệt kê tất cả quyền hạn có sẵn trong hệ thống."""
        token = await _get_admin_token(client)
        resp = await client.get("/api/v1/permissions", headers=_auth(token))
        assert resp.status_code == 200
        perms = resp.json()
        assert len(perms) > 0
        for perm in perms:
            for field in ("id", "name", "code", "module", "action"):
                assert field in perm

    async def test_assign_permissions_to_role(self, client: AsyncClient, db_session: AsyncSession) -> None:
        """Kiểm tra gán danh sách quyền cho vai trò."""
        token = await _get_admin_token(client)

        # 1. Tạo role mới
        role = Role(name="QA Manager", code="qa_manager")
        db_session.add(role)
        await db_session.flush()

        # 2. Lấy 2 permissions từ DB
        stmt = select(Permission).limit(2)
        res = await db_session.execute(stmt)
        perms = res.scalars().all()
        perm_ids = [str(p.id) for p in perms]

        # 3. Gán quyền
        assign_resp = await client.post(
            f"/api/v1/roles/{role.id}/permissions",
            json={"permission_ids": perm_ids},
            headers=_auth(token),
        )
        assert assign_resp.status_code == 200
        assert assign_resp.json()["success"] is True

        # 4. Kiểm tra chi tiết vai trò sau gán
        detail_resp = await client.get(f"/api/v1/roles/{role.id}", headers=_auth(token))
        detail_data = detail_resp.json()
        assert len(detail_data["permissions"]) == 2
        assigned_codes = [p["code"] for p in detail_data["permissions"]]
        expected_codes = [p.code for p in perms]
        assert set(assigned_codes) == set(expected_codes)


# ─── Super Admin Protections & Security Tests ─────────────────────────────────

class TestSecurityAndProtections:
    async def test_superadmin_role_cannot_be_deleted(self, client: AsyncClient, db_session: AsyncSession) -> None:
        """Không cho phép xóa vai trò super_admin."""
        token = await _get_admin_token(client)

        # Lấy ID của super_admin
        stmt = select(Role).where(Role.code == "super_admin")
        res = await db_session.execute(stmt)
        sa_role = res.scalar_one()

        resp = await client.delete(f"/api/v1/roles/{sa_role.id}", headers=_auth(token))
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "SYSTEM_ROLE_PROTECTED"

    async def test_system_roles_cannot_be_deleted(self, client: AsyncClient, db_session: AsyncSession) -> None:
        """Không cho phép xóa các vai trò hệ thống cố định (admin, editor, author)."""
        token = await _get_admin_token(client)

        for code in ("admin", "editor", "author"):
            stmt = select(Role).where(Role.code == code)
            res = await db_session.execute(stmt)
            role = res.scalar_one()

            resp = await client.delete(f"/api/v1/roles/{role.id}", headers=_auth(token))
            assert resp.status_code == 400
            assert resp.json()["error"]["code"] == "SYSTEM_ROLE_PROTECTED"

    async def test_superadmin_role_cannot_be_modified(self, client: AsyncClient, db_session: AsyncSession) -> None:
        """Không cho phép sửa đổi vai trò super_admin."""
        token = await _get_admin_token(client)

        stmt = select(Role).where(Role.code == "super_admin")
        res = await db_session.execute(stmt)
        sa_role = res.scalar_one()

        payload = {"name": "Hacker Admin", "description": "Modified Description"}
        resp = await client.put(f"/api/v1/roles/{sa_role.id}", json=payload, headers=_auth(token))
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "SUPERADMIN_ROLE_PROTECTED"

    async def test_superadmin_permissions_cannot_be_modified(self, client: AsyncClient, db_session: AsyncSession) -> None:
        """Không cho phép gỡ/thêm quyền thủ công cho vai trò super_admin."""
        token = await _get_admin_token(client)

        stmt = select(Role).where(Role.code == "super_admin")
        res = await db_session.execute(stmt)
        sa_role = res.scalar_one()

        resp = await client.post(
            f"/api/v1/roles/{sa_role.id}/permissions",
            json={"permission_ids": [str(uuid.uuid4())]},
            headers=_auth(token),
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "SUPERADMIN_ROLE_PROTECTED"

    async def test_rbac_denial_for_normal_user(self, client: AsyncClient, db_session: AsyncSession) -> None:
        """Người dùng thường không có quyền bị từ chối 403 khi gọi API quản trị vai trò."""
        from app.core.security import hash_password

        # Tạo user thường
        user = User(
            username="normal_user_test",
            email="normal_user@test.com",
            password_hash=hash_password("pass123"),
            full_name="Normal User",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Login
        login = await client.post("/api/v1/auth/login", json={"username": "normal_user_test", "password": "pass123"})
        user_token = login.json()["access_token"]

        # 1. Gọi GET /roles -> 403
        resp1 = await client.get("/api/v1/roles", headers=_auth(user_token))
        assert resp1.status_code == 403

        # 2. Gọi POST /roles -> 403
        resp2 = await client.post(
            "/api/v1/roles",
            json={"name": "Hacker Role", "code": "hacker"},
            headers=_auth(user_token),
        )
        assert resp2.status_code == 403

    async def test_role_with_assigned_users_cannot_be_deleted(self, client: AsyncClient, db_session: AsyncSession) -> None:
        """Không cho phép xóa vai trò nếu đang được gán cho người dùng."""
        token = await _get_admin_token(client)

        # 1. Tạo 1 role mới để test (không phải hệ thống)
        custom_role = Role(name="Temporary Role", code="temp_role_to_del")
        db_session.add(custom_role)
        await db_session.flush()

        # 2. Tạo 1 user mới
        from app.core.security import hash_password
        test_user = User(
            username="temp_user_roles_test",
            email="temp_user_roles_test@example.com",
            password_hash=hash_password("password123"),
            full_name="Temporary User",
            is_active=True,
        )
        db_session.add(test_user)
        await db_session.flush()

        # 3. Gán user vào role đó
        mapping = UserRole(user_id=test_user.id, role_id=custom_role.id)
        db_session.add(mapping)
        await db_session.commit()

        # 4. Thử xóa -> Phải bị lỗi ROLE_HAS_ASSIGNED_USERS
        resp = await client.delete(f"/api/v1/roles/{custom_role.id}", headers=_auth(token))
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "ROLE_HAS_ASSIGNED_USERS"

        # 5. Gỡ gán user khỏi role (xóa mapping)
        stmt_del = select(UserRole).where(UserRole.user_id == test_user.id, UserRole.role_id == custom_role.id)
        res_del = await db_session.execute(stmt_del)
        map_record = res_del.scalar_one()
        await db_session.delete(map_record)
        await db_session.commit()

        # 6. Thử xóa lại -> Phải thành công
        resp_again = await client.delete(f"/api/v1/roles/{custom_role.id}", headers=_auth(token))
        assert resp_again.status_code == 200
        assert resp_again.json()["success"] is True

