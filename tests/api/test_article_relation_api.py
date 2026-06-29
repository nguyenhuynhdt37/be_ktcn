import pytest
from httpx import AsyncClient

@pytest.fixture
async def admin_auth_headers(client: AsyncClient):
    login_res = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "adminpassword"})
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_article_relations(client: AsyncClient, admin_auth_headers):
    # 1. Create two articles
    article1_data = {"title": "Article 1", "content": "Content 1", "version": 1}
    article2_data = {"title": "Article 2", "content": "Content 2", "version": 1}
    
    resp1 = await client.post("/api/v1/articles/drafts", json=article1_data, headers=admin_auth_headers)
    resp2 = await client.post("/api/v1/articles/drafts", json=article2_data, headers=admin_auth_headers)
    
    a1_id = resp1.json()["id"]
    a2_id = resp2.json()["id"]
    
    # 2. Add relation
    relation_data = {
        "target_article_id": a2_id,
        "sort_order": 1
    }
    resp = await client.post(f"/api/v1/articles/{a1_id}/related", json=relation_data, headers=admin_auth_headers)
    assert resp.status_code == 201
    assert resp.json()["source_article_id"] == a1_id
    assert resp.json()["target_article_id"] == a2_id
    
    # 3. Duplicate relation (should fail)
    resp = await client.post(f"/api/v1/articles/{a1_id}/related", json=relation_data, headers=admin_auth_headers)
    assert resp.status_code == 400
    
    # 4. Self relation (should fail)
    self_relation = {"target_article_id": a1_id, "sort_order": 2}
    resp = await client.post(f"/api/v1/articles/{a1_id}/related", json=self_relation, headers=admin_auth_headers)
    assert resp.status_code == 400
    
    # 5. Update sort order
    update_data = {"sort_order": 5}
    resp = await client.patch(f"/api/v1/articles/{a1_id}/related/{a2_id}", json=update_data, headers=admin_auth_headers)
    assert resp.status_code == 200
    assert resp.json()["sort_order"] == 5
    
    # 6. Delete relation
    resp = await client.delete(f"/api/v1/articles/{a1_id}/related/{a2_id}", headers=admin_auth_headers)
    assert resp.status_code == 204
    
    # Delete again (should fail)
    resp = await client.delete(f"/api/v1/articles/{a1_id}/related/{a2_id}", headers=admin_auth_headers)
    assert resp.status_code == 404
