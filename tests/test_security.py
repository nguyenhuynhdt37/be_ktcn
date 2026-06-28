import pytest
from httpx import AsyncClient
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hashing():
    """
    Checks that password hashing and matching work correctly.
    """
    password = "secret-password"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_jwt_generation_and_decoding():
    """
    Checks that JWT tokens are generated with standard payload structure and successfully decoded.
    """
    subject = "user-12345"
    token = create_access_token(subject)
    decoded = decode_access_token(token)
    assert decoded["sub"] == subject
    assert "exp" in decoded
    assert "iat" in decoded


@pytest.mark.asyncio
async def test_auth_login_and_protected_endpoint(client: AsyncClient):
    """
    Tests the login endpoint and authorization check on /auth/me.
    """
    # 1. Login fail
    login_fail = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "wrongpassword"},
    )
    assert login_fail.status_code == 401

    # 2. Login success
    login_success = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "adminpassword"},
    )
    assert login_success.status_code == 200
    token_payload = login_success.json()
    assert "access_token" in token_payload
    token = token_payload["access_token"]

    # 3. Request protected /me without authorization header
    no_auth = await client.get("/api/v1/auth/me")
    assert no_auth.status_code == 403  # HTTPBearer returns 403 Forbidden when missing header

    # 4. Request protected /me with bad token
    bad_auth = await client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer invalidtoken"}
    )
    assert bad_auth.status_code == 401

    # 5. Request protected /me with valid token
    good_auth = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert good_auth.status_code == 200
    user_data = good_auth.json()
    assert user_data["username"] == "admin"
    assert user_data["role"] == "super_admin"
