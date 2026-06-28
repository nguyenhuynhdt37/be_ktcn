"""
Integration tests for Account Activity Monitoring API.

Tất cả endpoint chỉ dành cho Super Admin (require_superadmin).

Tests bao gồm:
  - GET  /users/{id}/sessions
  - GET  /users/{id}/login-history
  - POST /users/{id}/sessions/{s}/revoke
  - POST /users/{id}/sessions/revoke-all
  - POST /users/{id}/lock
  - POST /users/{id}/unlock
  - GET  /users/{id}/anomalies
  - RBAC: non-superadmin bị từ chối 403
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import LoginHistory, RefreshToken, User
from app.modules.auth.service import hash_token


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _get_superadmin_token(client: AsyncClient) -> str:
    """Lấy token của superadmin (seeded trong conftest)."""
    resp = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "adminpassword"})
    assert resp.status_code == 200, f"Login thất bại: {resp.text}"
    return resp.json()["access_token"]


async def _get_superadmin_id(client: AsyncClient, token: str) -> uuid.UUID:
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    return uuid.UUID(resp.json()["id"])


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ─── Sessions Endpoint ────────────────────────────────────────────────────────

class TestGetUserSessions:
    async def test_list_sessions_returns_list(self, client: AsyncClient) -> None:
        """Super Admin có thể lấy danh sách phiên đăng nhập của user."""
        token = await _get_superadmin_token(client)
        user_id = await _get_superadmin_id(client, token)

        resp = await client.get(f"/api/v1/users/{user_id}/sessions", headers=_auth(token))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_list_sessions_fields(self, client: AsyncClient) -> None:
        """Mỗi phiên trả về đủ các trường bắt buộc."""
        token = await _get_superadmin_token(client)
        user_id = await _get_superadmin_id(client, token)

        resp = await client.get(f"/api/v1/users/{user_id}/sessions", headers=_auth(token))
        assert resp.status_code == 200
        for session in resp.json():
            for field in ("id", "ip_address", "created_at", "expires_at", "is_revoked"):
                assert field in session, f"Trường '{field}' bị thiếu trong phản hồi sessions"

    async def test_list_sessions_requires_superadmin(self, client: AsyncClient, db_session: AsyncSession) -> None:
        """User thường bị từ chối 403."""
        from app.core.security import hash_password
        normal_user = User(
            username="normal_sessions_test",
            email="normal_sessions@test.com",
            password_hash=hash_password("pass123"),
            full_name="Normal User",
            is_active=True,
        )
        db_session.add(normal_user)
        await db_session.commit()
        await db_session.refresh(normal_user)

        login = await client.post("/api/v1/auth/login", json={"username": "normal_sessions_test", "password": "pass123"})
        assert login.status_code == 200
        normal_token = login.json()["access_token"]

        resp = await client.get(f"/api/v1/users/{normal_user.id}/sessions", headers=_auth(normal_token))
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "SUPERADMIN_REQUIRED"

    async def test_list_sessions_no_auth_returns_403(self, client: AsyncClient) -> None:
        """Không có token thì bị từ chối."""
        resp = await client.get(f"/api/v1/users/{uuid.uuid4()}/sessions")
        assert resp.status_code == 403


# ─── Login History Endpoint ───────────────────────────────────────────────────

class TestGetLoginHistory:
    async def test_login_history_returns_paginated(self, client: AsyncClient) -> None:
        """Lịch sử đăng nhập trả về cấu trúc phân trang đúng."""
        token = await _get_superadmin_token(client)
        user_id = await _get_superadmin_id(client, token)

        resp = await client.get(f"/api/v1/users/{user_id}/login-history", headers=_auth(token))
        assert resp.status_code == 200
        data = resp.json()
        for field in ("items", "total", "page", "page_size", "total_pages"):
            assert field in data, f"Trường '{field}' bị thiếu"

    async def test_login_history_has_records(self, client: AsyncClient) -> None:
        """Sau khi đăng nhập, phải có ít nhất 1 bản ghi lịch sử."""
        token = await _get_superadmin_token(client)
        user_id = await _get_superadmin_id(client, token)

        resp = await client.get(f"/api/v1/users/{user_id}/login-history", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    async def test_login_history_filter_success(self, client: AsyncClient) -> None:
        """Lọc status=success chỉ trả về bản ghi thành công."""
        token = await _get_superadmin_token(client)
        user_id = await _get_superadmin_id(client, token)

        resp = await client.get(
            f"/api/v1/users/{user_id}/login-history?status=success",
            headers=_auth(token),
        )
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["status"] == "success"

    async def test_login_history_pagination(self, client: AsyncClient) -> None:
        """Phân trang hoạt động đúng."""
        token = await _get_superadmin_token(client)
        user_id = await _get_superadmin_id(client, token)

        resp = await client.get(
            f"/api/v1/users/{user_id}/login-history?page=1&page_size=1",
            headers=_auth(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) <= 1
        assert data["page_size"] == 1


# ─── Revoke Single Session ────────────────────────────────────────────────────

class TestRevokeUserSession:
    async def test_revoke_existing_session(self, client: AsyncClient, db_session: AsyncSession) -> None:
        """Thu hồi một phiên cụ thể thành công."""
        token = await _get_superadmin_token(client)
        user_id = await _get_superadmin_id(client, token)

        fake = RefreshToken(
            user_id=user_id,
            token_hash=hash_token("fake-revoke-single-test-abc"),
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
            ip_address="10.0.0.1",
            user_agent="TestAgent/1.0",
            is_revoked=False,
        )
        db_session.add(fake)
        await db_session.commit()
        await db_session.refresh(fake)

        resp = await client.post(
            f"/api/v1/users/{user_id}/sessions/{fake.id}/revoke",
            headers=_auth(token),
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        await db_session.refresh(fake)
        assert fake.is_revoked is True, "Token phải được đánh dấu is_revoked=True"

    async def test_revoke_nonexistent_session_returns_404(self, client: AsyncClient) -> None:
        """Thu hồi phiên không tồn tại trả về 404."""
        token = await _get_superadmin_token(client)
        user_id = await _get_superadmin_id(client, token)

        resp = await client.post(
            f"/api/v1/users/{user_id}/sessions/{uuid.uuid4()}/revoke",
            headers=_auth(token),
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "SESSION_NOT_FOUND"


# ─── Revoke All Sessions ──────────────────────────────────────────────────────

class TestRevokeAllUserSessions:
    async def test_revoke_all_sessions_returns_count(self, client: AsyncClient, db_session: AsyncSession) -> None:
        """Thu hồi tất cả phiên trả về đúng số lượng đã revoke."""
        token = await _get_superadmin_token(client)
        user_id = await _get_superadmin_id(client, token)

        for i in range(2):
            fake = RefreshToken(
                user_id=user_id,
                token_hash=hash_token(f"fake-revoke-all-test-{i}-xyz99"),
                expires_at=datetime.now(timezone.utc) + timedelta(days=1),
                ip_address=f"10.0.1.{i}",
                is_revoked=False,
            )
            db_session.add(fake)
        await db_session.commit()

        resp = await client.post(
            f"/api/v1/users/{user_id}/sessions/revoke-all",
            headers=_auth(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert isinstance(data["revoked_count"], int)
        assert data["revoked_count"] >= 2


# ─── Lock / Unlock User ───────────────────────────────────────────────────────

class TestLockUnlockUser:
    async def test_lock_and_unlock_user(self, client: AsyncClient, db_session: AsyncSession) -> None:
        """Khoá → không thể login → mở khoá → đăng nhập thành công."""
        from app.core.security import hash_password

        test_user = User(
            username="locktest_activity_01",
            email="locktest_activity01@example.com",
            password_hash=hash_password("testpass123"),
            full_name="Lock Test User",
            is_active=True,
        )
        db_session.add(test_user)
        await db_session.commit()
        await db_session.refresh(test_user)

        admin_token = await _get_superadmin_token(client)

        # Khoá tài khoản
        lock = await client.post(f"/api/v1/users/{test_user.id}/lock", headers=_auth(admin_token))
        assert lock.status_code == 200
        assert lock.json()["is_active"] is False

        # Xác nhận không thể đăng nhập
        login_fail = await client.post(
            "/api/v1/auth/login",
            json={"username": "locktest_activity_01", "password": "testpass123"},
        )
        assert login_fail.status_code == 401, "Tài khoản bị khoá nhưng vẫn đăng nhập được"

        # Mở khoá
        unlock = await client.post(f"/api/v1/users/{test_user.id}/unlock", headers=_auth(admin_token))
        assert unlock.status_code == 200
        assert unlock.json()["is_active"] is True

        # Đăng nhập lại thành công
        login_ok = await client.post(
            "/api/v1/auth/login",
            json={"username": "locktest_activity_01", "password": "testpass123"},
        )
        assert login_ok.status_code == 200, "Tài khoản đã mở khoá nhưng không đăng nhập được"

    async def test_lock_nonexistent_user_returns_404(self, client: AsyncClient) -> None:
        """Khoá user không tồn tại trả về 404."""
        token = await _get_superadmin_token(client)
        resp = await client.post(f"/api/v1/users/{uuid.uuid4()}/lock", headers=_auth(token))
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "USER_NOT_FOUND"

    async def test_lock_revokes_active_sessions(self, client: AsyncClient, db_session: AsyncSession) -> None:
        """Khi khoá user, tất cả phiên active phải bị thu hồi."""
        from app.core.security import hash_password

        test_user = User(
            username="locktest_sessions_02",
            email="locktest_sessions02@example.com",
            password_hash=hash_password("testpass123"),
            full_name="Lock Session Test",
            is_active=True,
        )
        db_session.add(test_user)
        await db_session.commit()
        await db_session.refresh(test_user)

        active = RefreshToken(
            user_id=test_user.id,
            token_hash=hash_token("lock-session-test-active-xyz"),
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
            ip_address="192.168.1.1",
            is_revoked=False,
        )
        db_session.add(active)
        await db_session.commit()
        await db_session.refresh(active)

        admin_token = await _get_superadmin_token(client)
        await client.post(f"/api/v1/users/{test_user.id}/lock", headers=_auth(admin_token))

        await db_session.refresh(active)
        assert active.is_revoked is True, "Phiên không bị thu hồi sau khi khoá tài khoản"

    async def test_non_superadmin_cannot_lock(self, client: AsyncClient, db_session: AsyncSession) -> None:
        """User thường không thể khoá tài khoản."""
        from app.core.security import hash_password

        normal = User(
            username="cannot_lock_test_user",
            email="cannotlock@test.com",
            password_hash=hash_password("pass123"),
            full_name="Cannot Lock",
            is_active=True,
        )
        db_session.add(normal)
        await db_session.commit()
        await db_session.refresh(normal)

        login = await client.post(
            "/api/v1/auth/login", json={"username": "cannot_lock_test_user", "password": "pass123"}
        )
        normal_token = login.json()["access_token"]

        resp = await client.post(f"/api/v1/users/{normal.id}/lock", headers=_auth(normal_token))
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "SUPERADMIN_REQUIRED"


# ─── Anomaly Report ───────────────────────────────────────────────────────────

class TestAnomalyReport:
    async def test_anomaly_report_structure(self, client: AsyncClient) -> None:
        """Báo cáo trả về đúng cấu trúc."""
        token = await _get_superadmin_token(client)
        user_id = await _get_superadmin_id(client, token)

        resp = await client.get(f"/api/v1/users/{user_id}/anomalies", headers=_auth(token))
        assert resp.status_code == 200
        data = resp.json()
        for field in ("user_id", "risk_level", "anomalies", "active_session_count", "failed_login_count_24h", "generated_at"):
            assert field in data, f"Trường '{field}' bị thiếu"

    async def test_anomaly_risk_level_valid_values(self, client: AsyncClient) -> None:
        """Risk level phải nằm trong tập hợp hợp lệ."""
        token = await _get_superadmin_token(client)
        user_id = await _get_superadmin_id(client, token)

        resp = await client.get(f"/api/v1/users/{user_id}/anomalies", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json()["risk_level"] in ("SAFE", "LOW", "MEDIUM", "HIGH", "CRITICAL")

    async def test_brute_force_detected(self, client: AsyncClient, db_session: AsyncSession) -> None:
        """Phát hiện BRUTE_FORCE khi có ≥5 lần thất bại trong 15 phút."""
        token = await _get_superadmin_token(client)
        user_id = await _get_superadmin_id(client, token)
        now = datetime.now(timezone.utc)

        for i in range(6):
            db_session.add(LoginHistory(
                user_id=user_id,
                ip_address="5.5.5.5",
                user_agent="AttackerBot/1.0",
                status="failed",
                failure_reason="incorrect_credentials",
                created_at=now - timedelta(minutes=10 - i),
            ))
        await db_session.commit()

        resp = await client.get(f"/api/v1/users/{user_id}/anomalies", headers=_auth(token))
        assert resp.status_code == 200
        data = resp.json()
        types = [a["type"] for a in data["anomalies"]]
        assert "BRUTE_FORCE" in types, f"Không phát hiện BRUTE_FORCE. Anomalies: {types}"
        assert data["risk_level"] == "CRITICAL"

    async def test_anomaly_no_auth_returns_403(self, client: AsyncClient) -> None:
        """Không có token thì bị từ chối."""
        resp = await client.get(f"/api/v1/users/{uuid.uuid4()}/anomalies")
        assert resp.status_code == 403
