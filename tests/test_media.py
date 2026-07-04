import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import delete

from app.modules.media.models import MediaItem

test_media_ids = []

@pytest.fixture(autouse=True)
async def cleanup_data(db_session):
    global test_media_ids
    test_media_ids.clear()
    yield
    if test_media_ids:
        # Xóa đệ quy/xóa trực tiếp các bản ghi test trong database
        await db_session.execute(
            delete(MediaItem).where(MediaItem.id.in_(test_media_ids))
        )
        await db_session.commit()
    test_media_ids.clear()


@pytest.mark.asyncio
async def test_create_folder_api(client: AsyncClient, admin_headers: dict):
    payload = {
        "name": "Folder Test Automation",
        "parent_id": None
    }

    res = await client.post("/api/v1/admin/media/folders", json=payload, headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "id" in data
    assert data["name"] == "Folder Test Automation"
    assert data["is_folder"] is True
    test_media_ids.append(data["id"])


@pytest.mark.asyncio
async def test_list_directory_api(client: AsyncClient, admin_headers: dict):
    # Tạo folder trước
    payload = {
        "name": "Folder List Test",
        "parent_id": None
    }
    create_res = await client.post("/api/v1/admin/media/folders", json=payload, headers=admin_headers)
    assert create_res.status_code == 200
    folder_id = create_res.json()["id"]
    test_media_ids.append(folder_id)

    # List thư mục gốc
    res = await client.get("/api/v1/admin/media", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    # Tìm kiếm folder vừa tạo trong list
    found = any(item["id"] == folder_id for item in data)
    assert found is True


@pytest.mark.asyncio
async def test_rename_folder_api(client: AsyncClient, admin_headers: dict):
    # Tạo folder
    payload = {
        "name": "Folder Old Name",
        "parent_id": None
    }
    create_res = await client.post("/api/v1/admin/media/folders", json=payload, headers=admin_headers)
    folder_id = create_res.json()["id"]
    test_media_ids.append(folder_id)

    # Đổi tên
    rename_payload = {
        "name": "Folder New Name"
    }
    res = await client.post(f"/api/v1/admin/media/{folder_id}/rename", json=rename_payload, headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Folder New Name"


@pytest.mark.asyncio
async def test_move_folder_api(client: AsyncClient, admin_headers: dict):
    # Tạo folder cha 1
    create_res_1 = await client.post("/api/v1/admin/media/folders", json={"name": "Parent 1"}, headers=admin_headers)
    parent_1_id = create_res_1.json()["id"]
    test_media_ids.append(parent_1_id)

    # Tạo folder cha 2
    create_res_2 = await client.post("/api/v1/admin/media/folders", json={"name": "Parent 2"}, headers=admin_headers)
    parent_2_id = create_res_2.json()["id"]
    test_media_ids.append(parent_2_id)

    # Tạo folder con nằm trong Parent 1
    create_child = await client.post("/api/v1/admin/media/folders", json={"name": "Child Folder", "parent_id": parent_1_id}, headers=admin_headers)
    child_id = create_child.json()["id"]
    test_media_ids.append(child_id)

    # Di chuyển Child Folder sang Parent 2
    move_payload = {
        "parent_id": parent_2_id
    }
    res = await client.post(f"/api/v1/admin/media/{child_id}/move", json=move_payload, headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["parent_id"] == parent_2_id


@pytest.mark.asyncio
async def test_delete_folder_api(client: AsyncClient, admin_headers: dict):
    # Tạo folder
    create_res = await client.post("/api/v1/admin/media/folders", json={"name": "Folder To Delete"}, headers=admin_headers)
    folder_id = create_res.json()["id"]
    
    # Xóa folder
    res = await client.delete(f"/api/v1/admin/media/{folder_id}", headers=admin_headers)
    assert res.status_code == 200
    assert res.json() == {"success": True}
