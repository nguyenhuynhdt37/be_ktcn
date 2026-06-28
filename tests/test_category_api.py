import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.category.models import Category


async def _login(client: AsyncClient) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "adminpassword"},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_list_categories_success(client: AsyncClient, db_session: AsyncSession):
    # Tạo category trực tiếp trong DB với các trường SEO là None
    cat = Category(
        name="Tin tức sự kiện",
        slug="tin-tuc-su-kien",
        status="ACTIVE",
        is_visible=True,
        seo_title=None,
        seo_description=None
    )
    db_session.add(cat)
    await db_session.commit()

    token = await _login(client)
    
    response = await client.get(
        "/api/v1/categories",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Tin tức sự kiện"
    assert data[0]["slug"] == "tin-tuc-su-kien"
    # Kiểm tra xem fallback SEO có hoạt động không
    assert data[0]["seo_title"] is None
    assert data[0]["seo_description"] is None
    
    # Kiểm tra object seo_resolved chứa dữ liệu resolved 3 lớp
    assert data[0]["seo_resolved"] is not None
    assert data[0]["seo_resolved"]["seo_title"] == "Tin tức sự kiện | Trường Kỹ thuật và Công nghệ - Đại học Vinh"
    assert data[0]["seo_resolved"]["seo_description"] == "Trang thông tin chính thức của Trường Kỹ thuật và Công nghệ - Đại học Vinh."


@pytest.mark.asyncio
async def test_get_category_tree_success(client: AsyncClient, db_session: AsyncSession):
    # Tạo danh mục cha và con
    parent = Category(
        name="Đào tạo đại học",
        slug="dao-tao-dai-hoc",
        status="ACTIVE",
        is_visible=True,
    )
    db_session.add(parent)
    await db_session.flush()

    child = Category(
        name="Ngành CNTT",
        slug="nganh-cntt",
        parent_id=parent.id,
        status="ACTIVE",
        is_visible=True,
    )
    db_session.add(child)
    await db_session.commit()

    token = await _login(client)

    response = await client.get(
        "/api/v1/categories/tree",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Đào tạo đại học"
    
    # Kiểm tra đệ quy của tree
    assert len(data[0]["children"]) == 1
    assert data[0]["children"][0]["name"] == "Ngành CNTT"
    assert data[0]["children"][0]["seo_resolved"]["seo_title"] == "Ngành CNTT | Trường Kỹ thuật và Công nghệ - Đại học Vinh"


@pytest.mark.asyncio
async def test_create_category_success(client: AsyncClient, db_session: AsyncSession):
    token = await _login(client)

    response = await client.post(
        "/api/v1/categories",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Danh mục mới tạo",
            "slug": "danh-muc-moi-tao",
            "status": "ACTIVE",
            "is_visible": True,
        }
    )
    # Nếu bị lỗi 500, test này sẽ báo lỗi ngay lập tức!
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_reorder_categories_success(client: AsyncClient, db_session: AsyncSession):
    # Tạo 2 danh mục
    cat1 = Category(name="Danh mục 1", slug="danh-muc-1", sort_order=0)
    cat2 = Category(name="Danh mục 2", slug="danh-muc-2", sort_order=10)
    db_session.add_all([cat1, cat2])
    await db_session.commit()

    token = await _login(client)

    # Reorder (truyền parent_id là "" để test xem validator empty_str_to_none có hoạt động tốt không)
    response = await client.put(
        "/api/v1/categories/reorder",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "items": [
                {"id": str(cat1.id), "parent_id": "", "sort_order": 20},
                {"id": str(cat2.id), "parent_id": None, "sort_order": 10}
            ]
        }
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["success"] is True
    assert data["reordered"] == 2

