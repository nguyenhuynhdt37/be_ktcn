"""
Integration tests for GET /users/{id}/access-overview

Endpoint trả về tổng quan quyền truy cập của một tài khoản:
  - roles
  - permission_codes (toàn bộ mã quyền được cấp)
  - accessible_features (tính năng có thể truy cập, kèm quyền cụ thể từng tính năng)

Guard: require_superadmin → user thường bị 403 SUPERADMIN_REQUIRED
"""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert

from app.modules.auth.models import Feature, FeaturePermission, Permission, Role, RolePermission, User, UserRole


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _get_superadmin_token(client: AsyncClient) -> str:
    resp = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "adminpassword"})
    assert resp.status_code == 200, f"Login thất bại: {resp.text}"
    return resp.json()["access_token"]


async def _get_superadmin_id(client: AsyncClient, token: str) -> uuid.UUID:
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    return uuid.UUID(resp.json()["id"])


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ─── Access Overview — Cấu trúc Response ─────────────────────────────────────

class TestAccessOverviewStructure:
    async def test_returns_200_for_superadmin(self, client: AsyncClient) -> None:
        """Super Admin có thể lấy access overview của bất kỳ user nào."""
        token = await _get_superadmin_token(client)
        user_id = await _get_superadmin_id(client, token)

        resp = await client.get(f"/api/v1/users/{user_id}/access-overview", headers=_auth(token))
        assert resp.status_code == 200

    async def test_response_has_required_fields(self, client: AsyncClient) -> None:
        """Response phải chứa đầy đủ các trường bắt buộc."""
        token = await _get_superadmin_token(client)
        user_id = await _get_superadmin_id(client, token)

        resp = await client.get(f"/api/v1/users/{user_id}/access-overview", headers=_auth(token))
        assert resp.status_code == 200
        data = resp.json()

        for field in (
            "user_id", "username", "full_name", "is_active",
            "roles", "permission_codes", "accessible_features",
            "total_permissions", "total_accessible_features"
        ):
            assert field in data, f"Trường '{field}' bị thiếu trong response"

    async def test_user_id_matches_requested(self, client: AsyncClient) -> None:
        """user_id trong response phải khớp với id yêu cầu."""
        token = await _get_superadmin_token(client)
        user_id = await _get_superadmin_id(client, token)

        resp = await client.get(f"/api/v1/users/{user_id}/access-overview", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json()["user_id"] == str(user_id)

    async def test_nonexistent_user_returns_404(self, client: AsyncClient) -> None:
        """User không tồn tại trả về 404."""
        token = await _get_superadmin_token(client)

        resp = await client.get(f"/api/v1/users/{uuid.uuid4()}/access-overview", headers=_auth(token))
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "USER_NOT_FOUND"

    async def test_no_auth_returns_403(self, client: AsyncClient) -> None:
        """Không có token thì bị từ chối."""
        resp = await client.get(f"/api/v1/users/{uuid.uuid4()}/access-overview")
        assert resp.status_code == 403


# ─── Access Overview — Dữ liệu Roles & Permissions ───────────────────────────

class TestAccessOverviewData:
    async def test_superadmin_has_roles(self, client: AsyncClient) -> None:
        """Super Admin phải có ít nhất 1 role trong response."""
        token = await _get_superadmin_token(client)
        user_id = await _get_superadmin_id(client, token)

        resp = await client.get(f"/api/v1/users/{user_id}/access-overview", headers=_auth(token))
        data = resp.json()
        assert len(data["roles"]) >= 1
        # Superadmin phải có role super_admin
        role_codes = [r["code"] for r in data["roles"]]
        assert "super_admin" in role_codes

    async def test_permission_codes_is_list_of_strings(self, client: AsyncClient) -> None:
        """permission_codes phải là danh sách chuỗi."""
        token = await _get_superadmin_token(client)
        user_id = await _get_superadmin_id(client, token)

        resp = await client.get(f"/api/v1/users/{user_id}/access-overview", headers=_auth(token))
        data = resp.json()
        assert isinstance(data["permission_codes"], list)
        for code in data["permission_codes"]:
            assert isinstance(code, str), f"permission_code phải là string: {code}"

    async def test_total_permissions_matches_list(self, client: AsyncClient) -> None:
        """total_permissions phải bằng len(permission_codes)."""
        token = await _get_superadmin_token(client)
        user_id = await _get_superadmin_id(client, token)

        resp = await client.get(f"/api/v1/users/{user_id}/access-overview", headers=_auth(token))
        data = resp.json()
        assert data["total_permissions"] == len(data["permission_codes"])

    async def test_total_features_matches_list(self, client: AsyncClient) -> None:
        """total_accessible_features phải bằng len(accessible_features)."""
        token = await _get_superadmin_token(client)
        user_id = await _get_superadmin_id(client, token)

        resp = await client.get(f"/api/v1/users/{user_id}/access-overview", headers=_auth(token))
        data = resp.json()
        assert data["total_accessible_features"] == len(data["accessible_features"])

    async def test_permission_codes_are_sorted(self, client: AsyncClient) -> None:
        """permission_codes phải được sắp xếp theo thứ tự alphabet."""
        token = await _get_superadmin_token(client)
        user_id = await _get_superadmin_id(client, token)

        resp = await client.get(f"/api/v1/users/{user_id}/access-overview", headers=_auth(token))
        codes = resp.json()["permission_codes"]
        assert codes == sorted(codes), "permission_codes không được sắp xếp đúng thứ tự"


# ─── Access Overview — Cấu trúc Features ─────────────────────────────────────

class TestAccessibleFeaturesStructure:
    async def test_each_feature_has_required_fields(self, client: AsyncClient) -> None:
        """Mỗi feature trong accessible_features phải có đủ trường bắt buộc."""
        token = await _get_superadmin_token(client)
        user_id = await _get_superadmin_id(client, token)

        resp = await client.get(f"/api/v1/users/{user_id}/access-overview", headers=_auth(token))
        data = resp.json()

        for feature in data["accessible_features"]:
            for field in ("id", "name", "code", "sort_order", "is_visible", "granted_permissions"):
                assert field in feature, f"Trường '{field}' thiếu trong feature '{feature.get('code')}'"

    async def test_granted_permissions_per_feature_not_empty(self, client: AsyncClient) -> None:
        """Mỗi feature trong danh sách phải có ít nhất 1 quyền được cấp."""
        token = await _get_superadmin_token(client)
        user_id = await _get_superadmin_id(client, token)

        resp = await client.get(f"/api/v1/users/{user_id}/access-overview", headers=_auth(token))
        data = resp.json()

        for feature in data["accessible_features"]:
            assert len(feature["granted_permissions"]) >= 1, (
                f"Feature '{feature['code']}' trong danh sách nhưng không có quyền nào"
            )

    async def test_granted_permission_has_required_fields(self, client: AsyncClient) -> None:
        """Mỗi quyền trong granted_permissions phải có đủ trường bắt buộc."""
        token = await _get_superadmin_token(client)
        user_id = await _get_superadmin_id(client, token)

        resp = await client.get(f"/api/v1/users/{user_id}/access-overview", headers=_auth(token))
        data = resp.json()

        for feature in data["accessible_features"]:
            for perm in feature["granted_permissions"]:
                for field in ("id", "name", "code", "module", "action"):
                    assert field in perm, (
                        f"Trường '{field}' thiếu trong permission '{perm.get('code')}' của feature '{feature.get('code')}'"
                    )


# ─── Access Overview — Logic phân quyền đúng ────────────────────────────────

class TestAccessOverviewPermissionLogic:
    async def test_user_with_no_roles_has_no_features(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """User không có role nào thì accessible_features phải rỗng."""
        from app.core.security import hash_password

        no_role_user = User(
            username="no_role_access_test",
            email="norole_access@test.com",
            password_hash=hash_password("pass123"),
            full_name="No Role User",
            is_active=True,
        )
        db_session.add(no_role_user)
        await db_session.commit()
        await db_session.refresh(no_role_user)

        admin_token = await _get_superadmin_token(client)
        resp = await client.get(
            f"/api/v1/users/{no_role_user.id}/access-overview",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_permissions"] == 0
        assert data["accessible_features"] == []
        assert data["permission_codes"] == []

    async def test_user_with_role_sees_matching_features(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """
        User có role với 1 quyền cụ thể → chỉ thấy feature liên kết với quyền đó.
        Tạo feature, permission, role, gán cho user và kiểm tra.
        """
        from app.core.security import hash_password

        # Tạo permission
        perm = Permission(
            name="Test View Widget",
            code="widget.view",
            module="widget",
            action="view",
            description="Test permission for access overview",
        )
        db_session.add(perm)
        await db_session.flush()

        # Tạo feature và liên kết với permission
        feat = Feature(
            name="Widget Module",
            code="widget_test",
            route="/widgets",
            icon="widget-icon",
            sort_order=99,
            is_visible=True,
        )
        db_session.add(feat)
        await db_session.flush()

        db_session.add(FeaturePermission(feature_id=feat.id, permission_id=perm.id))

        # Tạo role và gán permission
        role = Role(
            name="Widget Viewer",
            code="widget_viewer_test",
            description="Test role",
        )
        db_session.add(role)
        await db_session.flush()

        db_session.add(RolePermission(role_id=role.id, permission_id=perm.id))

        # Tạo user và gán role
        test_user = User(
            username="widget_access_user",
            email="widget_access@test.com",
            password_hash=hash_password("pass123"),
            full_name="Widget User",
            is_active=True,
        )
        db_session.add(test_user)
        await db_session.flush()

        db_session.add(UserRole(user_id=test_user.id, role_id=role.id))
        await db_session.commit()

        admin_token = await _get_superadmin_token(client)
        resp = await client.get(
            f"/api/v1/users/{test_user.id}/access-overview",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()

        assert data["total_permissions"] == 1
        assert "widget.view" in data["permission_codes"]

        # Phải thấy đúng 1 feature (widget_test)
        feature_codes = [f["code"] for f in data["accessible_features"]]
        assert "widget_test" in feature_codes, (
            f"Feature 'widget_test' phải xuất hiện trong accessible_features. Có: {feature_codes}"
        )

        # Feature đó phải có quyền widget.view
        widget_feature = next(f for f in data["accessible_features"] if f["code"] == "widget_test")
        perm_codes = [p["code"] for p in widget_feature["granted_permissions"]]
        assert "widget.view" in perm_codes

    async def test_user_with_two_permissions_sees_both_in_feature(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """
        User có 2 quyền cùng thuộc 1 feature → feature đó có đủ 2 quyền trong granted_permissions.
        """
        from app.core.security import hash_password

        # 2 permissions
        perm_a = Permission(name="Multi View", code="multi_test.view", module="multi_test", action="view")
        perm_b = Permission(name="Multi Edit", code="multi_test.edit", module="multi_test", action="edit")
        db_session.add_all([perm_a, perm_b])
        await db_session.flush()

        # 1 feature liên kết với cả 2
        feat = Feature(
            name="Multi Test Feature",
            code="multi_test_feature",
            route="/multi",
            sort_order=100,
            is_visible=True,
        )
        db_session.add(feat)
        await db_session.flush()

        db_session.add(FeaturePermission(feature_id=feat.id, permission_id=perm_a.id))
        db_session.add(FeaturePermission(feature_id=feat.id, permission_id=perm_b.id))

        # Role có cả 2 quyền
        role = Role(name="Multi Role", code="multi_role_test")
        db_session.add(role)
        await db_session.flush()
        db_session.add(RolePermission(role_id=role.id, permission_id=perm_a.id))
        db_session.add(RolePermission(role_id=role.id, permission_id=perm_b.id))

        # User
        test_user = User(
            username="multi_perm_user_test",
            email="multi_perm@test.com",
            password_hash=hash_password("pass123"),
            full_name="Multi Perm User",
            is_active=True,
        )
        db_session.add(test_user)
        await db_session.flush()
        db_session.add(UserRole(user_id=test_user.id, role_id=role.id))
        await db_session.commit()

        admin_token = await _get_superadmin_token(client)
        resp = await client.get(
            f"/api/v1/users/{test_user.id}/access-overview",
            headers=_auth(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()

        multi_feat = next(
            (f for f in data["accessible_features"] if f["code"] == "multi_test_feature"), None
        )
        assert multi_feat is not None, "Feature 'multi_test_feature' phải xuất hiện"
        perm_codes = {p["code"] for p in multi_feat["granted_permissions"]}
        assert "multi_test.view" in perm_codes, "Quyền 'multi_test.view' phải có trong feature"
        assert "multi_test.edit" in perm_codes, "Quyền 'multi_test.edit' phải có trong feature"


# ─── RBAC Guard ──────────────────────────────────────────────────────────────

class TestAccessOverviewRBAC:
    async def test_non_superadmin_gets_403(self, client: AsyncClient, db_session: AsyncSession) -> None:
        """User thường bị từ chối với SUPERADMIN_REQUIRED."""
        from app.core.security import hash_password

        normal = User(
            username="normal_access_overview_test",
            email="normal_access_overview@test.com",
            password_hash=hash_password("pass123"),
            full_name="Normal User",
            is_active=True,
        )
        db_session.add(normal)
        await db_session.commit()
        await db_session.refresh(normal)

        login = await client.post(
            "/api/v1/auth/login",
            json={"username": "normal_access_overview_test", "password": "pass123"},
        )
        assert login.status_code == 200
        normal_token = login.json()["access_token"]

        resp = await client.get(
            f"/api/v1/users/{normal.id}/access-overview",
            headers=_auth(normal_token),
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "SUPERADMIN_REQUIRED"
