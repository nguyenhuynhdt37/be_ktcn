import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy import select
from app.modules.menu.models import Menu, MenuItem, MenuItemTranslation, MenuItemTargetType


@pytest.mark.asyncio
async def test_menu_lifecycle_and_i18n(client: AsyncClient, admin_headers: dict, db_session):
    """Test toàn bộ vòng đời của Menu và cấu hình đa ngôn ngữ (i18n) cho Menu Items."""
    
    # 1. Tạo Menu mới qua Admin API
    menu_code = f"menu_{uuid.uuid4().hex[:8]}"
    menu_payload = {
        "name": "Header Main Menu",
        "code": menu_code,
        "description": "Menu chính trên header website",
        "is_active": True
    }
    res_menu = await client.post("/api/v1/admin/menus", json=menu_payload, headers=admin_headers)
    assert res_menu.status_code == 201
    menu_data = res_menu.json()
    menu_id = menu_data["id"]
    
    # 2. Tạo Menu Item đa ngôn ngữ (Academics / Đào tạo)
    item_payload = {
        "parent_id": None,
        "target_type": None,
        "target_id": None,
        "external_url": None,
        "open_in_new_tab": False,
        "sort_order": 10,
        "is_visible": True,
        "translations": {
            "vi": {
                "title": "Đào tạo"
            },
            "en": {
                "title": "Academics"
            }
        }
    }
    res_item = await client.post(f"/api/v1/admin/menus/{menu_id}/items", json=item_payload, headers=admin_headers)
    assert res_item.status_code == 201
    item_data = res_item.json()
    item_id = item_data["id"]
    assert item_data["title"] == "Đào tạo"  # mặc định tiếng Việt ở Admin
    assert item_data["translations"]["en"]["title"] == "Academics"

    # 3. Lấy chi tiết Menu Item qua Admin API
    res_detail = await client.get(f"/api/v1/admin/menus/{menu_id}/items/{item_id}", headers=admin_headers)
    assert res_detail.status_code == 200
    assert res_detail.json()["translations"]["en"]["title"] == "Academics"

    # 4. Cập nhật bản dịch của Menu Item
    update_payload = {
        "translations": {
            "vi": {
                "title": "Chương trình đào tạo"
            },
            "en": {
                "title": "Academic Programs"
            }
        }
    }
    res_update = await client.put(f"/api/v1/admin/menus/{menu_id}/items/{item_id}", json=update_payload, headers=admin_headers)
    assert res_update.status_code == 200
    assert res_update.json()["translations"]["en"]["title"] == "Academic Programs"

    # 5. Gọi Portal API Tree lấy menu bằng tiếng Anh
    res_portal_en = await client.get(f"/api/v1/portal/menus/{menu_code}/tree?lang=en")
    assert res_portal_en.status_code == 200
    portal_en_data = res_portal_en.json()
    assert len(portal_en_data["items"]) == 1
    assert portal_en_data["items"][0]["title"] == "Academic Programs"
    assert "translations" not in portal_en_data["items"][0]  # không được expose translations

    # 6. Gọi Portal API Tree lấy menu bằng tiếng Việt
    res_portal_vi = await client.get(f"/api/v1/portal/menus/{menu_code}/tree?lang=vi")
    assert res_portal_vi.status_code == 200
    portal_vi_data = res_portal_vi.json()
    assert portal_vi_data["items"][0]["title"] == "Chương trình đào tạo"

    # 7. Test reorder (kéo thả) danh sách menu item
    # Tạo thêm một menu item con
    sub_item_payload = {
        "parent_id": item_id,
        "sort_order": 5,
        "translations": {
            "vi": { "title": "Công nghệ thông tin" }
        }
    }
    res_sub = await client.post(f"/api/v1/admin/menus/{menu_id}/items", json=sub_item_payload, headers=admin_headers)
    assert res_sub.status_code == 201
    sub_id = res_sub.json()["id"]

    reorder_payload = {
        "items": [
            {
                "id": sub_id,
                "parent_id": None,  # chuyển lên làm root
                "sort_order": 20
            }
        ]
    }
    res_reorder = await client.put(f"/api/v1/admin/menus/{menu_id}/items/reorder", json=reorder_payload, headers=admin_headers)
    assert res_reorder.status_code == 200

    # Dọn dẹp dữ liệu
    await db_session.execute(select(MenuItem).where(MenuItem.menu_id == uuid.UUID(menu_id)))
    # Cascade delete của SQLAlchemy / DB sẽ tự động dọn dẹp
    await db_session.delete(await db_session.get(Menu, uuid.UUID(menu_id)))
    await db_session.commit()
