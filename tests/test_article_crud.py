import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.modules.auth.models import Role, User, UserRole, Permission, RolePermission
from app.modules.category.models import Category
from app.modules.article.models import Article, Tag


@pytest.fixture
async def seed_category(db_session: AsyncSession) -> Category:
    """Seeds a test category for linking articles."""
    cat = Category(
        id=uuid.UUID("a1017cf7-88b3-4f9e-c616-3e4b3c75ad09"),
        name="Tin tức CNTT",
        slug="tin-tuc-cntt",
        description="Chuyên mục tin tức Công nghệ thông tin",
        status="ACTIVE",
        is_visible=True
    )
    db_session.add(cat)
    await db_session.commit()
    return cat


@pytest.fixture
async def seed_tags(db_session: AsyncSession) -> list:
    """Seeds two test tags."""
    t1 = Tag(id=uuid.UUID("e1017cf7-88b3-4f9e-c616-3e4b3c75ad91"), name="Công nghệ", slug="cong-nghe")
    t2 = Tag(id=uuid.UUID("e1017cf7-88b3-4f9e-c616-3e4b3c75ad92"), name="AI", slug="ai")
    db_session.add_all([t1, t2])
    await db_session.commit()
    return [t1, t2]


@pytest.fixture
async def seed_regular_user(db_session: AsyncSession) -> User:
    """Seeds a regular user with NO permissions."""
    role = Role(
        id=uuid.UUID("d1017cf7-88b3-4f9e-c616-3e4b3c75ad05"),
        name="Regular User",
        code="user",
        description="Regular user with no permissions",
    )
    db_session.add(role)

    user = User(
        id=uuid.UUID("3fa85f64-5717-4562-b3fc-2c963f66afa9"),
        username="regular",
        email="regular@university.edu.vn",
        password_hash=hash_password("regularpassword"),
        full_name="Regular User",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    mapping = UserRole(
        user_id=user.id,
        role_id=role.id,
    )
    db_session.add(mapping)
    await db_session.commit()
    return user


@pytest.fixture
async def admin_headers(client: AsyncClient) -> dict:
    """Authenticates as Super Admin and returns headers."""
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "adminpassword"}
    )
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def regular_headers(client: AsyncClient, seed_regular_user) -> dict:
    """Authenticates as Regular User and returns headers."""
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"username": "regular", "password": "regularpassword"}
    )
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_article_success(client: AsyncClient, seed_category, seed_tags, admin_headers):
    # Prepare create payload with tags, flags, and SEO metadata
    payload = {
        "category_id": str(seed_category.id),
        "title": "Khai giảng khóa học AI năm 2026",
        "slug": "khai-giang-ai-2026",
        "summary": "Tóm tắt khóa học AI ngắn hạn",
        "content": "Nội dung chi tiết khóa học AI...",
        "status": "DRAFT",
        "is_featured": True,
        "tag_ids": [str(tag.id) for tag in seed_tags],
        "seo_title": "SEO Khai giảng AI",
        "seo_description": "SEO description...",
        "seo_keywords": "ai, learning"
    }

    # Call POST API
    response = await client.post("/api/v1/articles", json=payload, headers=admin_headers)
    assert response.status_code == 201
    
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["slug"] == payload["slug"]
    assert data["is_featured"] is True
    assert len(data["tags"]) == 2
    assert data["seo_title"] == "SEO Khai giảng AI"
    assert data["view_count"] == 0


@pytest.mark.asyncio
async def test_create_article_duplicate_slug(client: AsyncClient, seed_category, admin_headers):
    # 1. Create first article
    payload1 = {
        "category_id": str(seed_category.id),
        "title": "Tin tuyển sinh",
        "slug": "tin-tuyen-sinh",
        "content": "Nội dung 1"
    }
    res1 = await client.post("/api/v1/articles", json=payload1, headers=admin_headers)
    assert res1.status_code == 201

    # 2. Create second article with same slug
    payload2 = {
        "category_id": str(seed_category.id),
        "title": "Tin tuyển sinh",
        "slug": "tin-tuyen-sinh",
        "content": "Nội dung 2"
    }
    res2 = await client.post("/api/v1/articles", json=payload2, headers=admin_headers)
    assert res2.status_code == 201
    data2 = res2.json()
    # The slug should be auto-appended with -1
    assert data2["slug"] == "tin-tuyen-sinh-1"


@pytest.mark.asyncio
async def test_get_article_detail(client: AsyncClient, seed_category, admin_headers):
    # Create article first
    payload = {
        "category_id": str(seed_category.id),
        "title": "Bài viết test detail",
        "content": "Nội dung chi tiết"
    }
    create_res = await client.post("/api/v1/articles", json=payload, headers=admin_headers)
    article_id = create_res.json()["id"]

    # Call GET detail
    detail_res = await client.get(f"/api/v1/articles/{article_id}", headers=admin_headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["title"] == payload["title"]


@pytest.mark.asyncio
async def test_update_article(client: AsyncClient, seed_category, seed_tags, admin_headers):
    # Create article
    payload = {
        "category_id": str(seed_category.id),
        "title": "Bài viết cũ",
        "content": "Nội dung cũ",
        "tag_ids": [str(seed_tags[0].id)]
    }
    create_res = await client.post("/api/v1/articles", json=payload, headers=admin_headers)
    article_id = create_res.json()["id"]

    # Update payload (swap tags, update title/SEO metadata)
    update_payload = {
        "title": "Bài viết mới đã sửa",
        "content": "Nội dung mới đã sửa",
        "tag_ids": [str(seed_tags[1].id)],
        "seo_title": "SEO Title mới"
    }

    # Call PATCH
    update_res = await client.patch(f"/api/v1/articles/{article_id}", json=update_payload, headers=admin_headers)
    assert update_res.status_code == 200
    
    data = update_res.json()
    assert data["title"] == update_payload["title"]
    assert data["content"] == update_payload["content"]
    assert len(data["tags"]) == 1
    assert data["tags"][0]["name"] == "AI"
    assert data["seo_title"] == "SEO Title mới"


@pytest.mark.asyncio
async def test_list_articles_filters_sorting_and_pagination(client: AsyncClient, seed_category, seed_tags, admin_headers, db_session: AsyncSession):
    # Create 3 articles with different stats and tags
    res1 = await client.post(
        "/api/v1/articles",
        json={
            "category_id": str(seed_category.id),
            "title": "Học máy cơ bản",
            "content": "Nội dung học máy...",
            "tag_ids": [str(seed_tags[0].id)],
            "is_featured": True
        },
        headers=admin_headers
    )
    id1 = uuid.UUID(res1.json()["id"])

    res2 = await client.post(
        "/api/v1/articles",
        json={
            "category_id": str(seed_category.id),
            "title": "Deep Learning nâng cao",
            "content": "Nội dung deep learning...",
            "tag_ids": [str(seed_tags[0].id), str(seed_tags[1].id)],
            "is_featured": False
        },
        headers=admin_headers
    )
    id2 = uuid.UUID(res2.json()["id"])

    res3 = await client.post(
        "/api/v1/articles",
        json={
            "category_id": str(seed_category.id),
            "title": "AI trong đời sống",
            "content": "Nội dung AI...",
            "tag_ids": [str(seed_tags[1].id)],
            "is_featured": True
        },
        headers=admin_headers
    )
    id3 = uuid.UUID(res3.json()["id"])

    # Cập nhật số lượt xem thủ công cho từng bài viết để kiểm thử sắp xếp
    from app.modules.article.models import ArticleStatus
    art1 = await db_session.get(Article, id1)
    art1.view_count = 100
    art1.status = ArticleStatus.PUBLISHED

    art2 = await db_session.get(Article, id2)
    art2.view_count = 500
    art2.status = ArticleStatus.PUBLISHED

    art3 = await db_session.get(Article, id3)
    art3.view_count = 50
    art3.status = ArticleStatus.PUBLISHED

    await db_session.commit()

    # 1. Test pagination: limit = 2
    res_paginated = await client.get("/api/v1/articles?limit=2", headers=admin_headers)
    assert res_paginated.status_code == 200
    assert len(res_paginated.json()["items"]) == 2

    # 2. Test filter by tag_slug='ai'
    res_tag = await client.get("/api/v1/articles?tag_slug=ai", headers=admin_headers)
    assert res_tag.status_code == 200
    titles = [a["title"] for a in res_tag.json()["items"]]
    assert "Deep Learning nâng cao" in titles
    assert "AI trong đời sống" in titles
    assert "Học máy cơ bản" not in titles

    # 3. Test filter by is_featured=True
    res_featured = await client.get("/api/v1/articles?is_featured=true", headers=admin_headers)
    assert res_featured.status_code == 200
    assert len(res_featured.json()["items"]) >= 2
    for art in res_featured.json()["items"]:
        assert art["is_featured"] is True

    # 4. Test sorting by views desc (should be: deep learning (500) -> học máy (100) -> ai đời sống (50))
    res_views = await client.get("/api/v1/articles?order_by=views&order_dir=desc", headers=admin_headers)
    assert res_views.status_code == 200
    art_list = res_views.json()["items"]
    # Find matching indexes
    ordered_titles = [a["title"] for a in art_list if a["title"] in ["Học máy cơ bản", "Deep Learning nâng cao", "AI trong đời sống"]]
    assert ordered_titles == ["Deep Learning nâng cao", "Học máy cơ bản", "AI trong đời sống"]


@pytest.mark.asyncio
async def test_soft_delete_article(client: AsyncClient, seed_category, admin_headers):
    # Create article
    create_res = await client.post(
        "/api/v1/articles",
        json={
            "category_id": str(seed_category.id),
            "title": "Bài viết sắp bị xóa",
            "content": "Nội dung..."
        },
        headers=admin_headers
    )
    article_id = create_res.json()["id"]

    # Delete article
    delete_res = await client.delete(f"/api/v1/articles/{article_id}", headers=admin_headers)
    assert delete_res.status_code == 204

    # After deletion, fetching should return 404
    get_res = await client.get(f"/api/v1/articles/{article_id}", headers=admin_headers)
    assert get_res.status_code == 404


@pytest.mark.asyncio
async def test_unauthorized_forbidden_actions(client: AsyncClient, seed_category, regular_headers):
    # Regular user tries to create article
    payload = {
        "category_id": str(seed_category.id),
        "title": "Bài viết của Regular",
        "content": "Nội dung..."
    }
    create_res = await client.post("/api/v1/articles", json=payload, headers=regular_headers)
    assert create_res.status_code == 403


@pytest.mark.asyncio
async def test_tags_endpoints_permissions(client: AsyncClient, admin_headers, regular_headers):
    # 1. Admin creates a tag successfully
    create_res = await client.post(
        "/api/v1/articles/tags",
        json={"name": "Thống kê dữ liệu"},
        headers=admin_headers
    )
    assert create_res.status_code == 201
    assert create_res.json()["name"] == "Thống kê dữ liệu"
    assert create_res.json()["slug"] == "thong-ke-du-lieu"

    # 2. Regular user tries to create a tag -> should fail with 403
    create_fail = await client.post(
        "/api/v1/articles/tags",
        json={"name": "Tag thất bại"},
        headers=regular_headers
    )
    assert create_fail.status_code == 403

    # 3. Admin lists tags successfully
    list_res = await client.get("/api/v1/articles/tags", headers=admin_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 4. Regular user tries to list tags -> should fail with 403
    list_fail = await client.get("/api/v1/articles/tags", headers=regular_headers)
    assert list_fail.status_code == 403




