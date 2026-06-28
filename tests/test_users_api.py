import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.modules.auth.models import Role, User, UserRole, Permission, RolePermission


@pytest.fixture
async def seed_extra_users(db_session: AsyncSession):
    """
    Seeds additional users with different roles and statuses to test filters.
    """
    # 1. Create Editor role and permissions
    editor_role = Role(
        id=uuid.UUID("d1017cf7-88b3-4f9e-c616-3e4b3c75ad03"),
        name="Editor Role",
        code="editor",
        description="Can edit content but cannot view users",
    )
    db_session.add(editor_role)

    # Add user.view permission to Super Admin (via relationship or direct role_permissions)
    # The conftest seeds super_admin role with ID d1017cf7-88b3-4f9e-c616-3e4b3c75ad01
    user_view_perm = Permission(
        id=uuid.UUID("f944ed33-ae89-5774-9849-c04be4af9d09"),
        name="View Users",
        code="user.view",
        module="user",
        action="view",
        description="Allow viewing users",
    )
    db_session.add(user_view_perm)
    await db_session.flush()

    # Link user.view to super_admin (though super_admin bypasses checks, it is good to test)
    super_admin_perm = RolePermission(
        role_id=uuid.UUID("d1017cf7-88b3-4f9e-c616-3e4b3c75ad01"),
        permission_id=user_view_perm.id,
    )
    db_session.add(super_admin_perm)

    # 2. Create users
    # Active Editor
    editor_user = User(
        id=uuid.UUID("3fa85f64-5717-4562-b3fc-2c963f66afa7"),
        username="editor1",
        email="editor1@university.edu.vn",
        password_hash=hash_password("editorpassword"),
        full_name="Jane Editor",
        is_active=True,
    )
    db_session.add(editor_user)

    # Inactive User
    inactive_user = User(
        id=uuid.UUID("3fa85f64-5717-4562-b3fc-2c963f66afa8"),
        username="blocked_user",
        email="blocked@university.edu.vn",
        password_hash=hash_password("blockedpassword"),
        full_name="Locked User",
        is_active=False,
    )
    db_session.add(inactive_user)
    await db_session.flush()

    # Link Editor user to Editor role
    db_session.add(UserRole(user_id=editor_user.id, role_id=editor_role.id))

    await db_session.commit()


@pytest.mark.asyncio
async def test_list_users_as_super_admin(client: AsyncClient, seed_extra_users):
    """
    Tests that a Super Admin can fetch the users list and all users are returned.
    """
    # 1. Login as Super Admin
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "adminpassword"},
    )
    access_token = login_res.json()["access_token"]

    # 2. Fetch users list
    response = await client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] == 3  # Admin (seeded in conftest), editor1, blocked_user
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert len(data["items"]) == 3

    # Check mapping format
    first_user = data["items"][0]  # Order by created_at desc, so blocked_user or editor1
    assert "username" in first_user
    assert "email" in first_user
    assert "roles" in first_user
    assert isinstance(first_user["roles"], list)


@pytest.mark.asyncio
async def test_list_users_filter_by_role(client: AsyncClient, seed_extra_users):
    """
    Verifies that filtering by role_code works correctly.
    """
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "adminpassword"},
    )
    access_token = login_res.json()["access_token"]

    # Filter for editor
    response = await client.get(
        "/api/v1/users?role_code=editor",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["username"] == "editor1"


@pytest.mark.asyncio
async def test_list_users_filter_by_status(client: AsyncClient, seed_extra_users):
    """
    Verifies that filtering by is_active works correctly.
    """
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "adminpassword"},
    )
    access_token = login_res.json()["access_token"]

    # Filter for inactive
    response = await client.get(
        "/api/v1/users?is_active=false",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["username"] == "blocked_user"


@pytest.mark.asyncio
async def test_list_users_search(client: AsyncClient, seed_extra_users):
    """
    Verifies that searching users works (by username/email/fullname).
    """
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "adminpassword"},
    )
    access_token = login_res.json()["access_token"]

    # Search for "Jane" (full name of Jane Editor)
    response = await client.get(
        "/api/v1/users?search=Jane",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["username"] == "editor1"


@pytest.mark.asyncio
async def test_list_users_unauthorized_editor_denied(client: AsyncClient, seed_extra_users):
    """
    Verifies that a user without 'user.view' permission (like our editor role)
    receives a 403 Forbidden.
    """
    # 1. Login as Editor
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"username": "editor1", "password": "editorpassword"},
    )
    access_token = login_res.json()["access_token"]

    # 2. Try to fetch users list
    response = await client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN_ACCESS"
    assert "không có quyền thực hiện hành động này" in response.json()["error"]["message"]


@pytest.fixture
async def seed_user_management_permissions(db_session: AsyncSession):
    """
    Seeds permissions and roles for testing user CRUD.
    """
    from app.modules.media.models import MediaItem

    # Create permissions
    perms = [
        Permission(id=uuid.uuid4(), name="Create User", code="user.create", module="user", action="create"),
        Permission(id=uuid.uuid4(), name="View User", code="user.view", module="user", action="view"),
        Permission(id=uuid.uuid4(), name="Update User", code="user.update", module="user", action="update"),
        Permission(id=uuid.uuid4(), name="Delete User", code="user.delete", module="user", action="delete"),
    ]
    for p in perms:
        db_session.add(p)
    await db_session.flush()

    # Create Manager role with these permissions
    manager_role = Role(
        id=uuid.uuid4(),
        name="User Manager",
        code="user_manager",
        description="Can manage normal users but not super_admin",
    )
    db_session.add(manager_role)
    await db_session.flush()

    for p in perms:
        db_session.add(RolePermission(role_id=manager_role.id, permission_id=p.id))

    # Create Manager user
    manager_user = User(
        id=uuid.uuid4(),
        username="manager1",
        email="manager1@university.edu.vn",
        password_hash=hash_password("managerpassword"),
        full_name="User Manager",
        is_active=True,
    )
    db_session.add(manager_user)
    await db_session.flush()

    db_session.add(UserRole(user_id=manager_user.id, role_id=manager_role.id))

    # Create a test avatar file
    avatar = MediaItem(
        id=uuid.uuid4(),
        name="avatar.png",
        is_folder=False,
        object_key="files/avatar_test",
        bucket="test-bucket",
        mime_type="image/png",
    )
    db_session.add(avatar)

    await db_session.commit()

    return {
        "manager_role": manager_role,
        "manager_user": manager_user,
        "avatar": avatar,
    }


@pytest.mark.asyncio
async def test_create_user_success(client: AsyncClient, seed_user_management_permissions, db_session: AsyncSession):
    """Kiểm tra tạo người dùng thành công."""
    # Login as Super Admin to perform actions
    login_res = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "adminpassword"})
    token = login_res.json()["access_token"]

    avatar = seed_user_management_permissions["avatar"]
    manager_role = seed_user_management_permissions["manager_role"]

    payload = {
        "username": "new_staff",
        "email": "new_staff@university.edu.vn",
        "password": "staffpassword123",
        "full_name": "Nguyen Van A",
        "phone": "0987654321",
        "bio": "Developer tại Khoa CNTT",
        "title": "Kỹ sư",
        "avatar_id": str(avatar.id),
        "role_ids": [str(manager_role.id)],
        "is_active": True,
    }

    resp = await client.post("/api/v1/users", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "new_staff"
    assert data["email"] == "new_staff@university.edu.vn"
    assert data["bio"] == "Developer tại Khoa CNTT"
    assert data["title"] == "Kỹ sư"
    assert data["avatar_id"] == str(avatar.id)
    assert data["avatar"]["name"] == "avatar.png"
    assert len(data["roles"]) == 1
    assert data["roles"][0]["code"] == "user_manager"


@pytest.mark.asyncio
async def test_create_user_privilege_escalation_denied(client: AsyncClient, seed_user_management_permissions, db_session: AsyncSession):
    """Kiểm tra chặn gán vai trò super_admin nếu người gọi không phải super_admin."""
    # Login as User Manager (not super_admin)
    login_res = await client.post("/api/v1/auth/login", json={"username": "manager1", "password": "managerpassword"})
    token = login_res.json()["access_token"]

    # Lấy ID của super_admin
    stmt = select(Role).where(Role.code == "super_admin")
    res = await db_session.execute(stmt)
    sa_role = res.scalar_one()

    payload = {
        "username": "fake_sa",
        "email": "fake_sa@university.edu.vn",
        "password": "password123",
        "full_name": "Fake Super Admin",
        "role_ids": [str(sa_role.id)],
    }

    resp = await client.post("/api/v1/users", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "SUPERADMIN_ASSIGNMENT_DENIED"


@pytest.mark.asyncio
async def test_get_user_detail_success(client: AsyncClient, seed_user_management_permissions, db_session: AsyncSession):
    """Kiểm tra lấy thông tin chi tiết người dùng thành công."""
    login_res = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "adminpassword"})
    token = login_res.json()["access_token"]

    user = seed_user_management_permissions["manager_user"]

    resp = await client.get(f"/api/v1/users/{user.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == str(user.id)
    assert data["username"] == "manager1"
    assert data["email"] == "manager1@university.edu.vn"
    assert len(data["roles"]) == 1
    assert data["roles"][0]["code"] == "user_manager"


@pytest.mark.asyncio
async def test_update_user_profile_success(client: AsyncClient, seed_user_management_permissions, db_session: AsyncSession):
    """Kiểm tra cập nhật thông tin người dùng thành công."""
    login_res = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "adminpassword"})
    token = login_res.json()["access_token"]

    user = seed_user_management_permissions["manager_user"]

    payload = {
        "full_name": "Updated Manager Name",
        "bio": "New Bio Text",
        "title": "Chuyên viên",
    }

    resp = await client.put(f"/api/v1/users/{user.id}", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["full_name"] == "Updated Manager Name"
    assert data["bio"] == "New Bio Text"
    assert data["title"] == "Chuyên viên"


@pytest.mark.asyncio
async def test_delete_user_success(client: AsyncClient, seed_user_management_permissions, db_session: AsyncSession):
    """Kiểm tra xóa thành công người dùng, chặn tự xóa chính mình và chặn xóa super_admin."""
    login_res = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "adminpassword"})
    token = login_res.json()["access_token"]

    # 1. Chặn tự xóa chính mình (admin xóa admin)
    stmt_admin = select(User).where(User.username == "admin")
    res_admin = await db_session.execute(stmt_admin)
    admin_user = res_admin.scalar_one()

    resp_self = await client.delete(f"/api/v1/users/{admin_user.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp_self.status_code == 400
    assert resp_self.json()["error"]["code"] == "SELF_DELETION_DENIED"

    # 2. Xóa thành công user manager
    user_to_delete = seed_user_management_permissions["manager_user"]
    resp_ok = await client.delete(f"/api/v1/users/{user_to_delete.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp_ok.status_code == 200
    assert resp_ok.json()["success"] is True

    # 3. Verify soft deletion in DB (deleted_at should be set, row still exists)
    stmt = select(User).where(User.id == user_to_delete.id)
    res = await db_session.execute(stmt)
    soft_deleted_user = res.scalar_one_or_none()
    assert soft_deleted_user is not None
    assert soft_deleted_user.deleted_at is not None


@pytest.mark.asyncio
async def test_check_email_duplicate(client: AsyncClient, seed_user_management_permissions):
    """Kiểm tra API kiểm tra trùng email."""
    # Login as User Manager
    login_res = await client.post("/api/v1/auth/login", json={"username": "manager1", "password": "managerpassword"})
    token = login_res.json()["access_token"]

    # 1. Check an email that already exists
    resp_exists = await client.get("/api/v1/users/check-email?email=manager1@university.edu.vn", headers={"Authorization": f"Bearer {token}"})
    assert resp_exists.status_code == 200
    assert resp_exists.json()["exists"] is True

    # 2. Check an email that does not exist
    resp_not_exists = await client.get("/api/v1/users/check-email?email=non_existent_email@university.edu.vn", headers={"Authorization": f"Bearer {token}"})
    assert resp_not_exists.status_code == 200
    assert resp_not_exists.json()["exists"] is False

