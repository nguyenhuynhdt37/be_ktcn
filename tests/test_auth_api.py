import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.modules.auth.models import RefreshToken, Role, User, UserRole


@pytest.mark.asyncio
async def test_login_success_sets_cookies(client: AsyncClient):
    """
    Tests that a successful login returns access_token in the body
    and sets the refresh_token in an HttpOnly cookie.
    """
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "adminpassword"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

    # Verify refresh_token cookie is present
    cookies = client.cookies
    assert "refresh_token" in cookies
    # Ensure cookie properties: httponly, secure, samesite
    # (FastAPI sets it via set_cookie header)
    cookie_header = response.headers.get("set-cookie", "")
    assert "HttpOnly" in cookie_header
    assert "SameSite=lax" in cookie_header


@pytest.mark.asyncio
async def test_login_incorrect_password(client: AsyncClient):
    """
    Verifies that logging in with an incorrect password returns 401.
    """
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INCORRECT_CREDENTIALS"


@pytest.mark.asyncio
async def test_refresh_token_rotation_workflow(client: AsyncClient):
    """
    Tests that accessing /refresh rotates the refresh token cookie and issues a new access token.
    """
    # 1. Login to set cookie
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "adminpassword"},
    )
    first_cookie = client.cookies.get("refresh_token")
    assert first_cookie is not None

    # 2. Call /refresh
    refresh_res = await client.post("/api/v1/auth/refresh")
    assert refresh_res.status_code == 200
    assert "access_token" in refresh_res.json()

    # 3. Verify a new refresh token cookie has been set (rotated)
    second_cookie = client.cookies.get("refresh_token")
    assert second_cookie is not None
    assert second_cookie != first_cookie


@pytest.mark.asyncio
async def test_refresh_token_rotation_breach_revokes_all(
    client: AsyncClient, db_session: AsyncSession
):
    """
    Tests that reusing a rotated refresh token triggers security breach actions,
    instantly revoking all active sessions for that user.
    """
    # 1. Login
    await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "adminpassword"},
    )
    first_cookie = client.cookies.get("refresh_token")

    # 2. Rotate once
    await client.post("/api/v1/auth/refresh")
    second_cookie = client.cookies.get("refresh_token")

    # 3. Simulate breach by manually injecting the first cookie back into the client
    client.cookies.set("refresh_token", first_cookie)

    # 4. Attempt to reuse first cookie
    breach_res = await client.post("/api/v1/auth/refresh")
    assert breach_res.status_code == 401
    assert "Phát hiện xâm nhập" in breach_res.json()["error"]["message"]

    # 5. Query DB to verify all sessions for this user have been marked as revoked
    result = await db_session.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == uuid.UUID("3fa85f64-5717-4562-b3fc-2c963f66afa6")
        )
    )
    tokens = result.scalars().all()
    assert len(tokens) == 2
    assert all(t.is_revoked is True for t in tokens)


@pytest.mark.asyncio
async def test_list_active_devices(client: AsyncClient):
    """
    Verifies that calling /devices returns active sessions and flags the current one.
    """
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "adminpassword"},
    )
    access_token = login_res.json()["access_token"]

    devices_res = await client.get(
        "/api/v1/auth/devices",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert devices_res.status_code == 200
    devices = devices_res.json()
    assert len(devices) == 1
    assert devices[0]["is_current"] is True


@pytest.mark.asyncio
async def test_revoke_device(client: AsyncClient, db_session: AsyncSession):
    """
    Verifies that a user can revoke a session using its device ID.
    """
    # 1. Login
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "adminpassword"},
    )
    access_token = login_res.json()["access_token"]

    # 2. Get device ID
    devices_res = await client.get(
        "/api/v1/auth/devices",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    device_id = devices_res.json()[0]["id"]

    # 3. Revoke device
    revoke_res = await client.post(
        f"/api/v1/auth/devices/{device_id}/revoke",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert revoke_res.status_code == 200
    assert revoke_res.json()["success"] is True

    # 4. Check DB state
    result = await db_session.execute(
        select(RefreshToken).where(RefreshToken.id == uuid.UUID(device_id))
    )
    token = result.scalar_one()
    assert token.is_revoked is True


@pytest.mark.asyncio
async def test_logout_revokes_current_session(client: AsyncClient):
    """
    Tests that /logout revokes the token and clears the client cookie.
    """
    # 1. Login
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "adminpassword"},
    )
    assert client.cookies.get("refresh_token") is not None
    access_token = login_res.json()["access_token"]

    # 2. Logout (now requires auth for audit logging)
    logout_res = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert logout_res.status_code == 200
    assert logout_res.json()["success"] is True

    # 3. Verify cookie is deleted and refresh fails
    assert client.cookies.get("refresh_token") is None
    refresh_fail = await client.post("/api/v1/auth/refresh")
    assert refresh_fail.status_code == 401


@pytest.mark.asyncio
async def test_logout_all_sessions(client: AsyncClient):
    """
    Verifies /logout-all terminates all sessions of the user.
    """
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "adminpassword"},
    )
    access_token = login_res.json()["access_token"]

    logout_all_res = await client.post(
        "/api/v1/auth/logout-all",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert logout_all_res.status_code == 200
    assert logout_all_res.json()["success"] is True
    assert client.cookies.get("refresh_token") is None
