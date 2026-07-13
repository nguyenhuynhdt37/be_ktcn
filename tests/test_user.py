import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.auth.models import User
from app.core.security import hash_password


@pytest.fixture(scope="function")
async def setup_test_users(db_session: AsyncSession):
    # 1. Tạo tài khoản admin riêng cho test này
    stmt_admin = select(User).where(User.username == "admin_restore_test")
    res_admin = await db_session.execute(stmt_admin)
    admin_user = res_admin.scalar_one_or_none()
    if not admin_user:
        admin_user = User(
            id=uuid.uuid4(),
            username="admin_restore_test",
            email="admin_restore@example.com",
            password_hash=hash_password("password"),
            full_name="Admin Restore Test",
            is_active=True,
            is_admin=True,
        )
        db_session.add(admin_user)
        await db_session.commit()
    else:
        admin_user.is_admin = True
        admin_user.is_active = True
        admin_user.deleted_at = None
        await db_session.commit()

    # 2. Tạo tài khoản member thường để test phân quyền
    stmt_member = select(User).where(User.username == "member_restore_test")
    res_member = await db_session.execute(stmt_member)
    member_user = res_member.scalar_one_or_none()
    if not member_user:
        member_user = User(
            id=uuid.uuid4(),
            username="member_restore_test",
            email="member_restore@example.com",
            password_hash=hash_password("password"),
            full_name="Member Restore Test",
            is_active=True,
            is_admin=False,
        )
        db_session.add(member_user)
        await db_session.commit()
    else:
        member_user.is_admin = False
        member_user.is_active = True
        member_user.deleted_at = None
        member_user.full_name = "Member Restore Test"  # Reset tên
        await db_session.commit()

    # 3. Tạo một tài khoản để thực hiện xóa mềm và khôi phục
    stmt_target = select(User).where(User.username == "user_to_restore")
    res_target = await db_session.execute(stmt_target)
    target_user = res_target.scalar_one_or_none()
    if not target_user:
        target_user = User(
            id=uuid.uuid4(),
            username="user_to_restore",
            email="target@example.com",
            password_hash=hash_password("password"),
            full_name="User To Restore",
            is_active=True,
            is_admin=False,
        )
        db_session.add(target_user)
        await db_session.commit()
    else:
        # Reset trạng thái
        target_user.deleted_at = None
        target_user.is_active = True
        await db_session.commit()

    yield {
        "admin_username": "admin_restore_test",
        "admin_password": "password",
        "member_id": member_user.id,
        "member_username": "member_restore_test",
        "member_password": "password",
        "target_id": target_user.id,
        "target_username": target_user.username
    }

    # Teardown: Xóa sạch các tài khoản test
    from sqlalchemy import delete
    from app.modules.auth.models import LoginHistory, RefreshToken
    from app.modules.audit.models import AuditLog
    
    async with db_session.begin_nested() if db_session.in_transaction() else db_session as session:
        for username in ["admin_restore_test", "member_restore_test", "user_to_restore"]:
            stmt = select(User).where(User.username == username)
            res = await db_session.execute(stmt)
            u = res.scalar_one_or_none()
            if u:
                await db_session.execute(delete(LoginHistory).where(LoginHistory.user_id == u.id))
                await db_session.execute(delete(RefreshToken).where(RefreshToken.user_id == u.id))
                await db_session.execute(delete(AuditLog).where(AuditLog.actor_id == u.id))
                await db_session.delete(u)
        await db_session.commit()


@pytest.mark.asyncio
async def test_user_restore_flow(client: AsyncClient, setup_test_users: dict, db_session: AsyncSession):
    test_data = setup_test_users
    target_id = test_data["target_id"]
    target_username = test_data["target_username"]

    # --- BƯỚC 1: Đăng nhập tài khoản Admin để lấy admin_headers ---
    login_admin = await client.post(
        "/api/v1/auth/login",
        json={"username": test_data["admin_username"], "password": test_data["admin_password"]},
    )
    assert login_admin.status_code == 200
    admin_token = login_admin.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    client.cookies.clear()

    # --- BƯỚC 2: Đăng nhập tài khoản Member để lấy member_headers ---
    login_member = await client.post(
        "/api/v1/auth/login",
        json={"username": test_data["member_username"], "password": test_data["member_password"]},
    )
    assert login_member.status_code == 200
    member_token = login_member.json()["access_token"]
    member_headers = {"Authorization": f"Bearer {member_token}"}
    client.cookies.clear()

    # --- BƯỚC 3: Admin xóa mềm tài khoản ---
    del_res = await client.delete(f"/api/v1/users/{target_id}", headers=admin_headers)
    assert del_res.status_code == 200
    assert del_res.json() == {"success": True}

    # --- BƯỚC 4: Lấy danh sách tài khoản bình thường (is_deleted=False) ---
    list_active = await client.get("/api/v1/users?is_deleted=false", headers=admin_headers)
    assert list_active.status_code == 200
    active_usernames = [u["username"] for u in list_active.json()["items"]]
    assert target_username not in active_usernames

    # --- BƯỚC 5: Thử lấy danh sách tài khoản đã xóa bằng quyền Member (Mong đợi 403) ---
    list_deleted_member = await client.get("/api/v1/users?is_deleted=true", headers=member_headers)
    assert list_deleted_member.status_code == 403

    # --- BƯỚC 6: Lấy danh sách tài khoản đã xóa bằng quyền Admin ---
    list_deleted_admin = await client.get("/api/v1/users?is_deleted=true", headers=admin_headers)
    assert list_deleted_admin.status_code == 200
    deleted_usernames = [u["username"] for u in list_deleted_admin.json()["items"]]
    assert target_username in deleted_usernames

    # --- BƯỚC 7: Thử khôi phục tài khoản bằng quyền Member (Mong đợi 403) ---
    restore_member = await client.post(f"/api/v1/users/{target_id}/restore", headers=member_headers)
    assert restore_member.status_code == 403

    # --- BƯỚC 8: Admin khôi phục tài khoản ---
    restore_admin = await client.post(f"/api/v1/users/{target_id}/restore", headers=admin_headers)
    assert restore_admin.status_code == 200
    restore_data = restore_admin.json()
    assert restore_data["username"] == target_username
    assert restore_data["is_active"] is True

    # Kiểm tra trong database thực tế
    db_session.expire_all()
    stmt = select(User).where(User.id == target_id)
    res = await db_session.execute(stmt)
    u_db = res.scalar_one()
    assert u_db.deleted_at is None
    assert u_db.is_active is True

    # --- BƯỚC 9: Kiểm tra lại tài khoản xuất hiện trong danh sách active ---
    list_active_after = await client.get("/api/v1/users?is_deleted=false", headers=admin_headers)
    assert list_active_after.status_code == 200
    active_usernames_after = [u["username"] for u in list_active_after.json()["items"]]
    assert target_username in active_usernames_after


@pytest.mark.asyncio
async def test_user_self_update_flow(client: AsyncClient, setup_test_users: dict, db_session: AsyncSession):
    test_data = setup_test_users
    target_id = test_data["target_id"]
    member_id = test_data["member_id"]

    # Đăng nhập tài khoản Member
    login_member = await client.post(
        "/api/v1/auth/login",
        json={"username": test_data["member_username"], "password": test_data["member_password"]},
    )
    assert login_member.status_code == 200
    member_token = login_member.json()["access_token"]
    member_headers = {"Authorization": f"Bearer {member_token}"}
    client.cookies.clear()

    # 1. Member tự sửa thông tin cá nhân của chính mình (Mong đợi 200)
    update_res = await client.put(
        f"/api/v1/users/{member_id}",
        json={"full_name": "Member Self Updated", "phone": "0987654321"},
        headers=member_headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["full_name"] == "Member Self Updated"
    assert update_res.json()["phone"] == "0987654321"

    # Kiểm tra trong DB
    db_session.expire_all()
    stmt_check = select(User).where(User.id == member_id)
    res_check = await db_session.execute(stmt_check)
    u_db = res_check.scalar_one()
    assert u_db.full_name == "Member Self Updated"
    assert u_db.phone == "0987654321"

    # 2. Member tự sửa thông tin và cố tình hack quyền is_admin=True (Mong đợi 200 nhưng is_admin vẫn là False)
    hack_res = await client.put(
        f"/api/v1/users/{member_id}",
        json={"is_admin": True, "full_name": "Member Hacker"},
        headers=member_headers,
    )
    assert hack_res.status_code == 200
    assert hack_res.json()["is_admin"] is False
    assert hack_res.json()["full_name"] == "Member Hacker"

    # Kiểm tra trong DB: is_admin vẫn phải là False
    db_session.expire_all()
    res_check_hack = await db_session.execute(stmt_check)
    u_db_hack = res_check_hack.scalar_one()
    assert u_db_hack.is_admin is False
    assert u_db_hack.full_name == "Member Hacker"

    # 3. Member thử chỉnh sửa thông tin của tài khoản khác (Mong đợi 403)
    edit_other_res = await client.put(
        f"/api/v1/users/{target_id}",
        json={"full_name": "Hack other user"},
        headers=member_headers,
    )
    assert edit_other_res.status_code == 403


@pytest.mark.asyncio
async def test_audit_logs_rbac_flow(client: AsyncClient, setup_test_users: dict):
    test_data = setup_test_users

    # Đăng nhập Admin
    login_admin = await client.post(
        "/api/v1/auth/login",
        json={"username": test_data["admin_username"], "password": test_data["admin_password"]},
    )
    assert login_admin.status_code == 200
    admin_token = login_admin.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    client.cookies.clear()

    # Đăng nhập Member
    login_member = await client.post(
        "/api/v1/auth/login",
        json={"username": test_data["member_username"], "password": test_data["member_password"]},
    )
    assert login_member.status_code == 200
    member_token = login_member.json()["access_token"]
    member_headers = {"Authorization": f"Bearer {member_token}"}
    client.cookies.clear()

    # 1. Gọi API audit logs bằng quyền Admin -> Mong đợi 200 OK
    res_admin = await client.get("/api/v1/admin/audit-logs", headers=admin_headers)
    assert res_admin.status_code == 200

    # 2. Gọi API audit logs bằng quyền Member -> Mong đợi 403 Forbidden
    res_member = await client.get("/api/v1/admin/audit-logs", headers=member_headers)
    assert res_member.status_code == 403


@pytest.mark.asyncio
async def test_profile_activity_and_dashboard_rbac_flow(client: AsyncClient, setup_test_users: dict):
    test_data = setup_test_users

    # Đăng nhập Admin
    login_admin = await client.post(
        "/api/v1/auth/login",
        json={"username": test_data["admin_username"], "password": test_data["admin_password"]},
    )
    assert login_admin.status_code == 200
    admin_token = login_admin.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    client.cookies.clear()

    # Đăng nhập Member
    login_member = await client.post(
        "/api/v1/auth/login",
        json={"username": test_data["member_username"], "password": test_data["member_password"]},
    )
    assert login_member.status_code == 200
    member_token = login_member.json()["access_token"]
    member_headers = {"Authorization": f"Bearer {member_token}"}
    client.cookies.clear()

    # 1. Gọi API profile activity bằng quyền Admin -> Mong đợi 200 OK
    res_profile_admin = await client.get("/api/v1/admin/profile/activity", headers=admin_headers)
    assert res_profile_admin.status_code == 200
    # 2. Gọi API profile activity bằng quyền Member -> Mong đợi 200 OK (Cá nhân vẫn được xem nhật ký của mình)
    res_profile_member = await client.get("/api/v1/admin/profile/activity", headers=member_headers)
    assert res_profile_member.status_code == 200
    # 3. Gọi API dashboard bằng quyền Admin -> Mong đợi 200 OK
    res_dash_admin = await client.get("/api/v1/admin/dashboard", headers=admin_headers)
    assert res_dash_admin.status_code == 200

    # 4. Gọi API dashboard bằng quyền Member -> Mong đợi 403 Forbidden
    res_dash_member = await client.get("/api/v1/admin/dashboard", headers=member_headers)
    assert res_dash_member.status_code == 403
