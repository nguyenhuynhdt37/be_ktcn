import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_academic_title_and_degree_list(client: AsyncClient, admin_headers: dict):
    # 1. Test Admin API của Academic Titles
    res_title_admin = await client.get("/api/v1/admin/academic-titles", headers=admin_headers)
    assert res_title_admin.status_code == 200
    titles_admin = res_title_admin.json()
    assert len(titles_admin) >= 2
    # Verify cấu trúc translations
    assert "translations" in titles_admin[0]
    assert "vi" in titles_admin[0]["translations"]
    assert "en" in titles_admin[0]["translations"]
    assert "name" in titles_admin[0]
    assert "abbreviation" in titles_admin[0]

    # 2. Test Portal API của Academic Titles
    res_title_portal = await client.get("/api/v1/portal/academic-titles?lang=en")
    assert res_title_portal.status_code == 200
    titles_portal = res_title_portal.json()
    assert len(titles_portal) >= 2
    # Kiểm tra đã dịch phẳng
    assert "translations" not in titles_portal[0]
    assert titles_portal[0]["name"] in ["Professor", "Associate Professor"]

    # 3. Test Admin API của Degrees
    res_degree_admin = await client.get("/api/v1/admin/degrees", headers=admin_headers)
    assert res_degree_admin.status_code == 200
    degrees_admin = res_degree_admin.json()
    assert len(degrees_admin) >= 6
    assert "translations" in degrees_admin[0]
    assert "vi" in degrees_admin[0]["translations"]
    assert "en" in degrees_admin[0]["translations"]

    # 4. Test Portal API của Degrees
    res_degree_portal = await client.get("/api/v1/portal/degrees?lang=en")
    assert res_degree_portal.status_code == 200
    degrees_portal = res_degree_portal.json()
    assert len(degrees_portal) >= 6
    assert "translations" not in degrees_portal[0]
    assert "sort_order" in degrees_portal[0]
