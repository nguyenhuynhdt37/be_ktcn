import pytest
from httpx import AsyncClient
from uuid import UUID

@pytest.fixture
async def admin_auth_headers(client: AsyncClient):
    login_res = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "adminpassword"})
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_article_draft_crud(client: AsyncClient, admin_auth_headers):
    # 1. Create Draft
    create_payload = {
        "title": "My first test article",
        "content": "<p>Hello World</p>"
    }
    res = await client.post("/api/v1/articles/drafts", json=create_payload, headers=admin_auth_headers)
    assert res.status_code == 201
    article = res.json()
    assert article["title"] == "My first test article"
    assert article["slug"] == "my-first-test-article"
    assert article["status"] == "DRAFT"
    assert article["version"] == 1
    
    article_id = article["id"]
    version = article["version"]
    
    # 2. Update Draft
    update_payload = {
        "content": "<p>Updated Content</p>",
        "version": version
    }
    res = await client.patch(f"/api/v1/articles/drafts/{article_id}", json=update_payload, headers=admin_auth_headers)
    assert res.status_code == 200
    updated = res.json()
    assert updated["version"] == version + 1
    
    # 3. Optimistic Locking Test (Using old version)
    res = await client.patch(f"/api/v1/articles/drafts/{article_id}", json=update_payload, headers=admin_auth_headers)
    assert res.status_code == 409
    
    # 4. List Articles
    res = await client.get("/api/v1/articles", headers=admin_auth_headers)
    assert res.status_code == 200
    assert len(res.json()) > 0
    
    # 5. Lock Article
    res = await client.post(f"/api/v1/articles/{article_id}/lock", headers=admin_auth_headers)
    assert res.status_code == 200
    locked = res.json()
    assert locked["locked_by"] is not None
