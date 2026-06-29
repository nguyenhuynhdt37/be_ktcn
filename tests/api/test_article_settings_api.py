import pytest
from httpx import AsyncClient

@pytest.fixture
async def admin_auth_headers(client: AsyncClient):
    login_res = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "adminpassword"})
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_update_article_settings(client: AsyncClient, admin_auth_headers):
    # 1. Create article
    article_data = {"title": "Settings Article", "content": "Content", "version": 1}
    resp = await client.post("/api/v1/articles/drafts", json=article_data, headers=admin_auth_headers)
    assert resp.status_code == 201
    article_id = resp.json()["id"]
    
    # 2. Update settings
    settings_data = {
        "is_featured": True,
        "is_pinned": True,
        "scheduled_unpublish_at": "2029-12-31T23:59:59Z"
    }
    
    resp = await client.patch(f"/api/v1/articles/{article_id}/settings", json=settings_data, headers=admin_auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_featured"] is True
    assert data["is_pinned"] is True
    assert data["scheduled_unpublish_at"] is not None
