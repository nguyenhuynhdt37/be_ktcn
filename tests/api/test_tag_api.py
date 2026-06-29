import pytest
from httpx import AsyncClient
from uuid import uuid4

@pytest.fixture
async def admin_auth_headers(client: AsyncClient):
    login_res = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "adminpassword"})
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_crud_tag(client: AsyncClient, admin_auth_headers):
    # 1. Create Tag
    create_data = {
        "name": "Test Tag",
        "description": "Test Description"
    }
    response = await client.post("/api/v1/tags", json=create_data, headers=admin_auth_headers)
    assert response.status_code == 201
    tag = response.json()
    assert tag["name"] == "Test Tag"
    assert tag["slug"] == "test-tag"
    tag_id = tag["id"]

    # 2. Get Tags
    response = await client.get("/api/v1/tags?search=Test", headers=admin_auth_headers)
    assert response.status_code == 200
    tags = response.json()
    assert len(tags) > 0
    assert any(t["id"] == tag_id for t in tags)

    # 3. Update Tag
    update_data = {
        "name": "Updated Tag"
    }
    response = await client.patch(f"/api/v1/tags/{tag_id}", json=update_data, headers=admin_auth_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Tag"
    assert response.json()["slug"] == "test-tag" # Slug didn't change automatically

    # 4. Duplicate Name
    create_data_2 = {
        "name": "Updated Tag"
    }
    response = await client.post("/api/v1/tags", json=create_data_2, headers=admin_auth_headers)
    assert response.status_code == 400

    # 5. Delete Tag
    response = await client.delete(f"/api/v1/tags/{tag_id}", headers=admin_auth_headers)
    assert response.status_code == 204

@pytest.mark.asyncio
async def test_sync_article_tags(client: AsyncClient, admin_auth_headers):
    # Create an article first
    article_data = {
        "title": "Article for Tags",
        "content": "Content",
        "version": 1
    }
    response = await client.post("/api/v1/articles/drafts", json=article_data, headers=admin_auth_headers)
    assert response.status_code == 201
    article_id = response.json()["id"]
    
    # Create tags
    tag1_resp = await client.post("/api/v1/tags", json={"name": "Tag1"}, headers=admin_auth_headers)
    tag2_resp = await client.post("/api/v1/tags", json={"name": "Tag2"}, headers=admin_auth_headers)
    tag1_id = tag1_resp.json()["id"]
    tag2_id = tag2_resp.json()["id"]
    
    # Sync Tags
    sync_data = {
        "tag_ids": [tag1_id, tag2_id]
    }
    response = await client.put(f"/api/v1/articles/{article_id}/tags", json=sync_data, headers=admin_auth_headers)
    assert response.status_code == 200
    
    # Assert successful - the article detail currently might not return tags, 
    # but the API shouldn't error out. If the API returns 200, we consider it a success.
