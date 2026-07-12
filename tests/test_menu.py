import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy import select, delete
from app.modules.menu.models import Menu, MenuItem
from app.modules.category.models import Category, CategoryTranslation


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
        "target_type": "EXTERNAL_LINK",
        "target_id": None,
        "open_in_new_tab": False,
        "sort_order": 10,
        "is_visible": True,
        "translations": {
            "vi": {
                "title": "Đào tạo",
                "external_url": "https://google.com/vi"
            },
            "en": {
                "title": "Academics",
                "external_url": "https://google.com/en"
            }
        }
    }
    res_item = await client.post(f"/api/v1/admin/menus/{menu_id}/items", json=item_payload, headers=admin_headers)
    assert res_item.status_code == 201
    item_data = res_item.json()
    item_id = item_data["id"]
    assert item_data["title"] == "Đào tạo"  # mặc định tiếng Việt ở Admin
    assert item_data["translations"]["vi"]["external_url"] == "https://google.com/vi"
    assert item_data["translations"]["en"]["title"] == "Academics"
    assert item_data["translations"]["en"]["external_url"] == "https://google.com/en"

    # 3. Lấy chi tiết Menu Item qua Admin API
    res_detail = await client.get(f"/api/v1/admin/menus/{menu_id}/items/{item_id}", headers=admin_headers)
    assert res_detail.status_code == 200
    assert res_detail.json()["translations"]["en"]["title"] == "Academics"
    assert res_detail.json()["translations"]["en"]["external_url"] == "https://google.com/en"

    # 4. Cập nhật bản dịch của Menu Item
    update_payload = {
        "translations": {
            "vi": {
                "title": "Chương trình đào tạo",
                "external_url": "https://new-google.com/vi"
            },
            "en": {
                "title": "Academic Programs",
                "external_url": "https://new-google.com/en"
            }
        }
    }
    res_update = await client.put(f"/api/v1/admin/menus/{menu_id}/items/{item_id}", json=update_payload, headers=admin_headers)
    assert res_update.status_code == 200
    assert res_update.json()["translations"]["en"]["title"] == "Academic Programs"
    assert res_update.json()["translations"]["en"]["external_url"] == "https://new-google.com/en"

    # 5. Gọi Portal API Tree lấy menu bằng tiếng Anh
    res_portal_en = await client.get(f"/api/v1/portal/menus/{menu_code}/tree?lang=en")
    assert res_portal_en.status_code == 200
    portal_en_data = res_portal_en.json()
    assert len(portal_en_data["items"]) == 1
    assert portal_en_data["items"][0]["title"] == "Academic Programs"
    assert portal_en_data["items"][0]["external_url"] == "https://new-google.com/en"
    assert "translations" not in portal_en_data["items"][0]  # không được expose translations

    # 6. Gọi Portal API Tree lấy menu bằng tiếng Việt
    res_portal_vi = await client.get(f"/api/v1/portal/menus/{menu_code}/tree?lang=vi")
    assert res_portal_vi.status_code == 200
    portal_vi_data = res_portal_vi.json()
    assert portal_vi_data["items"][0]["title"] == "Chương trình đào tạo"
    assert portal_vi_data["items"][0]["external_url"] == "https://new-google.com/vi"

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


@pytest.mark.asyncio
async def test_portal_menu_tree_target_translation_i18n(client: AsyncClient, admin_headers: dict, db_session):
    """Test Portal Menu API lấy cây menu đã dịch kèm thông tin target_info được dịch tự động."""
    
    # 1. Tạo một Category với các bản dịch đa ngôn ngữ qua Admin API
    cat_payload = {
        "parent_id": None,
        "status": "ACTIVE",
        "is_visible": True,
        "thumbnail_id": None,
        "is_weekly_schedule": False,
        "sort_order": 10,
        "translations": {
            "vi": {
                "name": "Mạng máy tính",
                "slug": "mang-may-tinh",
                "description": "Bộ môn mạng"
            },
            "en": {
                "name": "Computer Networks",
                "slug": "computer-networks",
                "description": "Department of Computer Networks"
            }
        }
    }
    res_cat = await client.post("/api/v1/admin/categories", json=cat_payload, headers=admin_headers)
    assert res_cat.status_code == 201
    cat_data = res_cat.json()
    category_id = cat_data["id"]

    # 2. Tạo Menu mới
    menu_code = f"menu_target_{uuid.uuid4().hex[:8]}"
    menu_payload = {
        "name": "Header Main Menu Target",
        "code": menu_code,
        "description": "Menu chính",
        "is_active": True
    }
    res_menu = await client.post("/api/v1/admin/menus", json=menu_payload, headers=admin_headers)
    assert res_menu.status_code == 201
    menu_id = res_menu.json()["id"]

    # 3. Tạo Menu Item liên kết với Category vừa tạo
    item_payload = {
        "parent_id": None,
        "target_type": "CATEGORY",
        "target_id": category_id,
        "external_url": None,
        "open_in_new_tab": False,
        "sort_order": 10,
        "is_visible": True,
        "translations": {
            "vi": {
                "title": "Chương trình đào tạo"
            },
            "en": {
                "title": "Academic Programs"
            }
        }
    }
    res_item = await client.post(f"/api/v1/admin/menus/{menu_id}/items", json=item_payload, headers=admin_headers)
    assert res_item.status_code == 201
    item_id = res_item.json()["id"]

    # 4. Gọi Portal API Tree lấy menu bằng tiếng Anh (lang=en)
    res_portal_en = await client.get(f"/api/v1/portal/menus/{menu_code}/tree?lang=en")
    assert res_portal_en.status_code == 200
    portal_en_data = res_portal_en.json()
    assert len(portal_en_data["items"]) == 1
    menu_item_en = portal_en_data["items"][0]
    
    assert menu_item_en["title"] == "Academic Programs"
    assert menu_item_en["target_type"] == "CATEGORY"
    assert menu_item_en["target_id"] == category_id
    
    # Kiểm tra target_info đã được dịch sang tiếng Anh và format PortalTargetInfo
    assert menu_item_en["target_info"] is not None
    assert menu_item_en["target_info"]["title"] == "Computer Networks"
    assert menu_item_en["target_info"]["slug"].startswith("computer-networks")
    # Đảm bảo không expose các thông tin admin của target
    assert "id" not in menu_item_en["target_info"]
    assert "type" not in menu_item_en["target_info"]
    assert "status" not in menu_item_en["target_info"]
    assert "path" not in menu_item_en["target_info"]

    # 5. Gọi Portal API Tree lấy menu bằng tiếng Việt (lang=vi)
    res_portal_vi = await client.get(f"/api/v1/portal/menus/{menu_code}/tree?lang=vi")
    assert res_portal_vi.status_code == 200
    portal_vi_data = res_portal_vi.json()
    menu_item_vi = portal_vi_data["items"][0]
    
    assert menu_item_vi["title"] == "Chương trình đào tạo"
    assert menu_item_vi["target_info"]["title"] == "Mạng máy tính"
    assert menu_item_vi["target_info"]["slug"].startswith("mang-may-tinh")

    # Dọn dẹp dữ liệu
    await db_session.execute(delete(MenuItem).where(MenuItem.menu_id == uuid.UUID(menu_id)))
    await db_session.delete(await db_session.get(Menu, uuid.UUID(menu_id)))
    await db_session.execute(delete(CategoryTranslation).where(CategoryTranslation.category_id == uuid.UUID(category_id)))
    await db_session.delete(await db_session.get(Category, uuid.UUID(category_id)))
    await db_session.commit()
