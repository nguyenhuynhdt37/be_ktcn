"""
Tests cho Menu ↔ Category Target Linking.
Kiểm tra: validation target, resolve target_info, batch resolve trong tree, error cases.
"""
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.category.models import Category
from app.modules.menu.models import Menu, MenuItem


# ──────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────


async def _login(client: AsyncClient) -> str:
    """Login và trả về access_token."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "adminpassword"},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    """Helper tạo header Authorization."""
    return {"Authorization": f"Bearer {token}"}


async def _create_menu(client: AsyncClient, token: str, code: str = "test-menu") -> dict:
    """Helper tạo menu mới."""
    resp = await client.post(
        "/api/v1/menus",
        json={"name": "Test Menu", "code": code, "is_active": True},
        headers=_auth(token),
    )
    assert resp.status_code == 201
    return resp.json()


async def _create_category(
    db: AsyncSession,
    name: str = "Tin tức",
    slug: str = "tin-tuc",
    status: str = "ACTIVE",
    parent_id: uuid.UUID | None = None,
) -> Category:
    """Helper tạo category trực tiếp vào DB."""
    cat = Category(
        name=name,
        slug=slug,
        status=status,
        is_visible=True,
        parent_id=parent_id,
    )
    db.add(cat)
    await db.flush()
    await db.commit()
    return cat


# ──────────────────────────────────────────────
# Test Cases: Create Menu Item with Category Target
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_item_with_category_target(client: AsyncClient, db_session: AsyncSession):
    """Tạo menu item liên kết Category ACTIVE → thành công, response có target_info."""
    token = await _login(client)
    menu = await _create_menu(client, token)
    cat = await _create_category(db_session, name="Tuyển sinh", slug="tuyen-sinh")

    resp = await client.post(
        f"/api/v1/menus/{menu['id']}/items",
        json={
            "title": "Tuyển sinh",
            "target_type": "CATEGORY",
            "target_id": str(cat.id),
            "sort_order": 10,
        },
        headers=_auth(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["target_type"] == "CATEGORY"
    assert data["target_id"] == str(cat.id)
    assert data["has_link"] is True

    # Kiểm tra target_info được resolve
    assert data["target_info"] is not None
    assert data["target_info"]["name"] == "Tuyển sinh"
    assert data["target_info"]["slug"] == "tuyen-sinh"
    assert data["target_info"]["status"] == "ACTIVE"
    assert data["target_info"]["type"] == "CATEGORY"


@pytest.mark.asyncio
async def test_create_item_with_inactive_category_fails(client: AsyncClient, db_session: AsyncSession):
    """Tạo menu item liên kết Category DRAFT → lỗi 400."""
    token = await _login(client)
    menu = await _create_menu(client, token)
    cat = await _create_category(db_session, name="Bản nháp", slug="ban-nhap", status="DRAFT")

    resp = await client.post(
        f"/api/v1/menus/{menu['id']}/items",
        json={
            "title": "Link sai",
            "target_type": "CATEGORY",
            "target_id": str(cat.id),
            "sort_order": 10,
        },
        headers=_auth(token),
    )
    assert resp.status_code == 400
    assert "TARGET_CATEGORY_NOT_ACTIVE" in resp.text


@pytest.mark.asyncio
async def test_create_item_with_nonexistent_target_fails(client: AsyncClient, db_session: AsyncSession):
    """Tạo menu item liên kết target_id không tồn tại → lỗi 404."""
    token = await _login(client)
    menu = await _create_menu(client, token)
    fake_id = str(uuid.uuid4())

    resp = await client.post(
        f"/api/v1/menus/{menu['id']}/items",
        json={
            "title": "Link ảo",
            "target_type": "CATEGORY",
            "target_id": fake_id,
            "sort_order": 10,
        },
        headers=_auth(token),
    )
    assert resp.status_code == 404
    assert "TARGET_CATEGORY_NOT_FOUND" in resp.text


@pytest.mark.asyncio
async def test_create_item_with_deleted_category_fails(client: AsyncClient, db_session: AsyncSession):
    """Tạo menu item liên kết Category đã bị xóa mềm → lỗi 400."""
    token = await _login(client)
    menu = await _create_menu(client, token)
    cat = await _create_category(db_session, name="Đã xóa", slug="da-xoa", status="ACTIVE")

    # Xóa mềm category
    from datetime import datetime, UTC
    cat.deleted_at = datetime.now(UTC)
    db_session.add(cat)
    await db_session.commit()

    resp = await client.post(
        f"/api/v1/menus/{menu['id']}/items",
        json={
            "title": "Link xóa",
            "target_type": "CATEGORY",
            "target_id": str(cat.id),
            "sort_order": 10,
        },
        headers=_auth(token),
    )
    assert resp.status_code == 400
    assert "TARGET_CATEGORY_DELETED" in resp.text


# ──────────────────────────────────────────────
# Test Cases: Update Menu Item Target
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_item_change_target(client: AsyncClient, db_session: AsyncSession):
    """Đổi target_id sang Category khác → validate thành công, target_info cập nhật."""
    token = await _login(client)
    menu = await _create_menu(client, token)
    cat_a = await _create_category(db_session, name="Cat A", slug="cat-a")
    cat_b = await _create_category(db_session, name="Cat B", slug="cat-b")

    # Tạo item liên kết cat_a
    resp = await client.post(
        f"/api/v1/menus/{menu['id']}/items",
        json={
            "title": "Link A",
            "target_type": "CATEGORY",
            "target_id": str(cat_a.id),
            "sort_order": 10,
        },
        headers=_auth(token),
    )
    assert resp.status_code == 201
    item_id = resp.json()["id"]

    # Đổi sang cat_b
    resp = await client.put(
        f"/api/v1/menus/{menu['id']}/items/{item_id}",
        json={"target_id": str(cat_b.id)},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["target_info"]["name"] == "Cat B"
    assert data["target_info"]["slug"] == "cat-b"


# ──────────────────────────────────────────────
# Test Cases: Tree Response Target Info
# ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_tree_response_includes_target_info(client: AsyncClient, db_session: AsyncSession):
    """GET tree → response có target_info.name, target_info.slug, target_info.path."""
    token = await _login(client)
    menu = await _create_menu(client, token)

    # Tạo category cha/con
    parent_cat = await _create_category(db_session, name="Đào tạo", slug="dao-tao")
    child_cat = await _create_category(
        db_session, name="Sau Đại học", slug="sau-dai-hoc", parent_id=parent_cat.id
    )

    # Tạo 2 menu items liên kết
    await client.post(
        f"/api/v1/menus/{menu['id']}/items",
        json={
            "title": "Menu Đào tạo",
            "target_type": "CATEGORY",
            "target_id": str(parent_cat.id),
            "sort_order": 10,
        },
        headers=_auth(token),
    )
    await client.post(
        f"/api/v1/menus/{menu['id']}/items",
        json={
            "title": "Menu SĐH",
            "target_type": "CATEGORY",
            "target_id": str(child_cat.id),
            "sort_order": 20,
        },
        headers=_auth(token),
    )

    # Tạo 1 label item (không liên kết)
    await client.post(
        f"/api/v1/menus/{menu['id']}/items",
        json={
            "title": "Label đơn giản",
            "sort_order": 30,
        },
        headers=_auth(token),
    )

    # GET tree
    resp = await client.get(
        f"/api/v1/menus/{menu['id']}/tree",
        headers=_auth(token),
    )
    assert resp.status_code == 200
    data = resp.json()

    items = data["items"]
    assert len(items) == 3

    # Item 1: Đào tạo
    item_dao_tao = next(i for i in items if i["title"] == "Menu Đào tạo")
    assert item_dao_tao["target_info"]["name"] == "Đào tạo"
    assert item_dao_tao["target_info"]["path"] == "Đào tạo"

    # Item 2: Sau Đại học — path phải có breadcrumb
    item_sdh = next(i for i in items if i["title"] == "Menu SĐH")
    assert item_sdh["target_info"]["name"] == "Sau Đại học"
    assert item_sdh["target_info"]["path"] == "Đào tạo / Sau Đại học"

    # Item 3: Label — không có target_info
    item_label = next(i for i in items if i["title"] == "Label đơn giản")
    assert item_label["target_info"] is None
    assert item_label["has_link"] is False


@pytest.mark.asyncio
async def test_create_item_without_target_works(client: AsyncClient, db_session: AsyncSession):
    """Tạo menu item label (không liên kết target) → thành công, target_info = null."""
    token = await _login(client)
    menu = await _create_menu(client, token)

    resp = await client.post(
        f"/api/v1/menus/{menu['id']}/items",
        json={"title": "Label nhóm", "sort_order": 10},
        headers=_auth(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["target_type"] is None
    assert data["target_id"] is None
    assert data["target_info"] is None
    assert data["has_link"] is False


@pytest.mark.asyncio
async def test_create_item_external_link_no_target_validation(client: AsyncClient, db_session: AsyncSession):
    """Tạo menu item EXTERNAL_LINK → không cần validate target, target_info = null."""
    token = await _login(client)
    menu = await _create_menu(client, token)

    resp = await client.post(
        f"/api/v1/menus/{menu['id']}/items",
        json={
            "title": "Facebook",
            "target_type": "EXTERNAL_LINK",
            "external_url": "https://facebook.com",
            "open_in_new_tab": True,
            "sort_order": 10,
        },
        headers=_auth(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["target_type"] == "EXTERNAL_LINK"
    assert data["external_url"] == "https://facebook.com"
    assert data["target_info"] is None
    assert data["has_link"] is True
