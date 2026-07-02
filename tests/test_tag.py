import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select, delete

from app.modules.tag.models import Tag, TagTranslation

test_tag_ids = []

@pytest.fixture(autouse=True)
async def cleanup_data(db_session):
    global test_tag_ids
    test_tag_ids.clear()
    yield
    if test_tag_ids:
        await db_session.execute(
            delete(TagTranslation).where(TagTranslation.tag_id.in_(test_tag_ids))
        )
        await db_session.execute(
            delete(Tag).where(Tag.id.in_(test_tag_ids))
        )
        await db_session.commit()
    test_tag_ids.clear()


@pytest.mark.asyncio
async def test_create_tag_api(client: AsyncClient, admin_headers: dict):
    payload = {
        "color": "#FF5733",
        "sort_order": 1,
        "is_active": True,
        "translations": {
            "vi": {
                "name": "Nhãn Tiếng Việt",
                "slug": "nhan-tieng-viet",
                "description": "Mô tả nhãn"
            },
            "en": {
                "name": "English Tag",
                "slug": "english-tag",
                "description": "Tag description"
            }
        }
    }

    res = await client.post("/api/v1/admin/tags", json=payload, headers=admin_headers)
    assert res.status_code == 201
    data = res.json()
    assert "id" in data
    test_tag_ids.append(data["id"])

    assert data["color"] == "#FF5733"
    assert data["translations"]["vi"]["name"] == "Nhãn Tiếng Việt"
    assert data["translations"]["en"]["name"] == "English Tag"
    assert data["is_translated"]["vi"] is True
    assert data["is_translated"]["en"] is True


@pytest.mark.asyncio
async def test_update_tag_api(client: AsyncClient, admin_headers: dict):
    # 1. Tạo tag nháp ban đầu
    create_payload = {
        "color": "#FF5733",
        "translations": {
            "vi": {
                "name": "Nhãn gốc",
                "slug": "nhan-goc",
                "description": "Mô tả gốc"
            }
        }
    }
    res = await client.post("/api/v1/admin/tags", json=create_payload, headers=admin_headers)
    tag_id = res.json()["id"]
    test_tag_ids.append(tag_id)

    # 2. Update thêm tiếng Anh
    update_payload = {
        "color": "#00FF00",
        "translations": {
            "vi": {
                "name": "Nhãn gốc đã sửa",
                "slug": "nhan-goc-da-sua",
                "description": "Mô tả gốc đã sửa"
            },
            "en": {
                "name": "English Tag Updated",
                "slug": "english-tag-updated",
                "description": "English description updated"
            }
        }
    }

    res_up = await client.put(f"/api/v1/admin/tags/{tag_id}", json=update_payload, headers=admin_headers)
    assert res_up.status_code == 200
    data = res_up.json()
    assert data["color"] == "#00FF00"
    assert data["translations"]["vi"]["name"] == "Nhãn gốc đã sửa"
    assert data["translations"]["en"]["name"] == "English Tag Updated"
    assert data["is_translated"]["en"] is True


@pytest.mark.asyncio
async def test_portal_list_tags_api(client: AsyncClient, admin_headers: dict):
    # Tạo tag qua admin API
    payload = {
        "color": "#FF5733",
        "translations": {
            "vi": {
                "name": "Nhãn tiếng Việt",
                "slug": "tag-vi",
                "description": "Nội dung vi"
            },
            "en": {
                "name": "English name",
                "slug": "tag-en",
                "description": "English desc"
            }
        }
    }
    res = await client.post("/api/v1/admin/tags", json=payload, headers=admin_headers)
    tag_id = res.json()["id"]
    test_tag_ids.append(tag_id)

    # 1. Gọi Portal API list_tags với lang=vi
    portal_res_vi = await client.get(f"/api/v1/portal/tags?lang=vi")
    assert portal_res_vi.status_code == 200
    data_vi = portal_res_vi.json()
    # Tìm tag vừa tạo
    tag_vi = next((t for t in data_vi["items"] if t["id"] == tag_id), None)
    assert tag_vi is not None
    assert tag_vi["name"] == "Nhãn tiếng Việt"
    assert tag_vi["slug"] == "tag-vi"

    # 2. Gọi Portal API list_tags với lang=en
    portal_res_en = await client.get(f"/api/v1/portal/tags?lang=en")
    assert portal_res_en.status_code == 200
    data_en = portal_res_en.json()
    tag_en = next((t for t in data_en["items"] if t["id"] == tag_id), None)
    assert tag_en is not None
    assert tag_en["name"] == "English name"
    assert tag_en["slug"] == "tag-en"
