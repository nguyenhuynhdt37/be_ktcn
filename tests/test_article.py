import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select, delete
from datetime import datetime, timezone

from app.modules.article.models import Article, ArticleTranslation, ArticleStatus
from app.modules.category.models import Category
from app.modules.language.models import Language

test_article_ids = []
test_category_ids = []

@pytest.fixture(autouse=True)
async def cleanup_data(db_session):
    global test_article_ids, test_category_ids
    test_article_ids.clear()
    test_category_ids.clear()
    yield
    if test_article_ids:
        await db_session.execute(
            delete(ArticleTranslation).where(ArticleTranslation.article_id.in_(test_article_ids))
        )
        await db_session.execute(
            delete(Article).where(Article.id.in_(test_article_ids))
        )
    if test_category_ids:
        await db_session.execute(
            delete(Category).where(Category.id.in_(test_category_ids))
        )
    await db_session.commit()


@pytest.mark.asyncio
async def test_create_article_api(client: AsyncClient, admin_headers: dict, db_session):
    # Tạo category trước
    category = Category(
        status="ACTIVE",
        is_visible=True,
        sort_order=1
    )
    db_session.add(category)
    await db_session.commit()
    test_category_ids.append(category.id)

    payload = {
        "category_id": str(category.id),
        "status": "PUBLISHED",
        "is_draft": False,
        "is_featured": True,
        "translations": {
            "vi": {
                "title": "Bài viết Tiếng Việt",
                "slug": "bai-viet-tieng-viet",
                "content": "<p>Nội dung tiếng Việt</p>",
                "excerpt": "Tóm tắt tiếng Việt",
                "seo_title": "SEO Việt"
            },
            "en": {
                "title": "English Article",
                "slug": "english-article",
                "content": "<p>English Content</p>",
                "excerpt": "English Excerpt",
                "seo_title": "SEO English"
            }
        }
    }

    res = await client.post("/api/v1/admin/articles", json=payload, headers=admin_headers)
    assert res.status_code == 201
    data = res.json()
    assert "id" in data
    test_article_ids.append(data["id"])

    assert data["status"] == "PUBLISHED"
    assert data["is_draft"] is False
    assert data["translations"]["vi"]["title"] == "Bài viết Tiếng Việt"
    assert data["translations"]["en"]["title"] == "English Article"
    assert data["is_translated"]["vi"] is True
    assert data["is_translated"]["en"] is True


@pytest.mark.asyncio
async def test_update_article_api(client: AsyncClient, admin_headers: dict, db_session):
    # Tạo category trước
    category = Category(
        status="ACTIVE",
        is_visible=True,
        sort_order=1
    )
    db_session.add(category)
    await db_session.commit()
    test_category_ids.append(category.id)

    # 1. Tạo article ban đầu
    create_payload = {
        "category_id": str(category.id),
        "status": "DRAFT",
        "is_draft": True,
        "translations": {
            "vi": {
                "title": "Bài gốc",
                "slug": "bai-goc",
                "content": "Nội dung gốc",
            }
        }
    }
    res = await client.post("/api/v1/admin/articles", json=create_payload, headers=admin_headers)
    art_id = res.json()["id"]
    test_article_ids.append(art_id)

    # 2. Cập nhật thêm tiếng Anh
    update_payload = {
        "is_draft": False,
        "status": "PUBLISHED",
        "translations": {
            "vi": {
                "title": "Bài gốc đã sửa",
                "slug": "bai-goc-da-sua",
                "content": "Nội dung gốc đã sửa",
            },
            "en": {
                "title": "Updated English Title",
                "slug": "updated-english-title",
                "content": "Updated English content",
            }
        }
    }

    res_up = await client.put(f"/api/v1/admin/articles/{art_id}", json=update_payload, headers=admin_headers)
    assert res_up.status_code == 200
    data = res_up.json()
    assert data["translations"]["vi"]["title"] == "Bài gốc đã sửa"
    assert data["translations"]["en"]["title"] == "Updated English Title"
    assert data["is_translated"]["en"] is True


@pytest.mark.asyncio
async def test_portal_get_article_by_slug_api(client: AsyncClient, admin_headers: dict, db_session):
    # Tạo category
    category = Category(status="ACTIVE", is_visible=True, sort_order=1)
    db_session.add(category)
    await db_session.commit()
    test_category_ids.append(category.id)

    # Tạo article
    payload = {
        "category_id": str(category.id),
        "status": "PUBLISHED",
        "is_draft": False,
        "translations": {
            "vi": {
                "title": "Bài tiếng Việt",
                "slug": "slug-vi",
                "content": "Nội dung vi"
            },
            "en": {
                "title": "English title",
                "slug": "slug-en",
                "content": "English content"
            }
        }
    }
    res = await client.post("/api/v1/admin/articles", json=payload, headers=admin_headers)
    assert res.status_code == 201
    created_data = res.json()
    art_id = created_data["id"]
    test_article_ids.append(art_id)
    
    slug_vi = created_data["translations"]["vi"]["slug"]
    slug_en = created_data["translations"]["en"]["slug"]

    # 1. Gọi Portal API với lang=vi
    portal_res_vi = await client.get(f"/api/v1/portal/articles/{slug_vi}?lang=vi")
    assert portal_res_vi.status_code == 200
    data_vi = portal_res_vi.json()
    assert data_vi["title"] == "Bài tiếng Việt"
    assert data_vi["slug"] == slug_vi

    # 2. Gọi Portal API với lang=en
    portal_res_en = await client.get(f"/api/v1/portal/articles/{slug_en}?lang=en")
    assert portal_res_en.status_code == 200
    data_en = portal_res_en.json()
    assert data_en["title"] == "English title"
    assert data_en["slug"] == slug_en


@pytest.mark.asyncio
async def test_delete_article_api(client: AsyncClient, admin_headers: dict, db_session):
    # Tạo category
    category = Category(status="ACTIVE", is_visible=True, sort_order=1)
    db_session.add(category)
    await db_session.commit()
    test_category_ids.append(category.id)

    # Tạo article
    payload = {
        "category_id": str(category.id),
        "status": "PUBLISHED",
        "is_draft": False,
        "translations": {
            "vi": {
                "title": "Bài viết cần xóa",
                "slug": "bai-viet-can-xoa",
                "content": "Nội dung"
            }
        }
    }
    res = await client.post("/api/v1/admin/articles", json=payload, headers=admin_headers)
    art_id = res.json()["id"]
    test_article_ids.append(art_id)

    # Gọi API delete bài viết
    delete_res = await client.delete(f"/api/v1/admin/articles/{art_id}", headers=admin_headers)
    assert delete_res.status_code == 204

    # Lấy lại chi tiết bài viết (Admin) -> Mong đợi 404 (do đã bị xóa mềm)
    get_res = await client.get(f"/api/v1/admin/articles/{art_id}", headers=admin_headers)
    assert get_res.status_code == 404


@pytest.mark.asyncio
async def test_list_my_drafts_api(client: AsyncClient, admin_headers: dict, db_session):
    # Tạo category
    category = Category(status="ACTIVE", is_visible=True, sort_order=1)
    db_session.add(category)
    await db_session.commit()
    test_category_ids.append(category.id)

    # Tạo bài viết nháp
    payload = {
        "category_id": str(category.id),
        "status": "DRAFT",
        "is_draft": True,
        "translations": {
            "vi": {
                "title": "Bài viết nháp test list",
                "slug": "bai-viet-nhap-test-list",
                "content": "Nội dung"
            }
        }
    }
    res = await client.post("/api/v1/admin/articles", json=payload, headers=admin_headers)
    assert res.status_code == 201
    art_id = res.json()["id"]
    test_article_ids.append(art_id)

    # Gọi API lấy danh sách bài viết nháp
    drafts_res = await client.get("/api/v1/admin/articles/drafts?page=1&page_size=10", headers=admin_headers)
    assert drafts_res.status_code == 200
    data = drafts_res.json()
    assert data["total_items"] >= 1
    assert data["items"][0]["id"] == art_id


@pytest.mark.asyncio
async def test_archive_and_publish_article_api(client: AsyncClient, admin_headers: dict, db_session):
    # Tạo category
    category = Category(status="ACTIVE", is_visible=True, sort_order=1)
    db_session.add(category)
    await db_session.commit()
    test_category_ids.append(category.id)

    # Tạo article ở trạng thái PUBLISHED
    payload = {
        "category_id": str(category.id),
        "status": "PUBLISHED",
        "is_draft": False,
        "translations": {
            "vi": {
                "title": "Bài viết test archive",
                "slug": "bai-viet-test-archive",
                "content": "Nội dung"
            }
        }
    }
    res = await client.post("/api/v1/admin/articles", json=payload, headers=admin_headers)
    assert res.status_code == 201
    art_id = res.json()["id"]
    test_article_ids.append(art_id)

    # 1. Gọi PATCH /archive
    archive_res = await client.patch(f"/api/v1/admin/articles/{art_id}/archive", headers=admin_headers)
    assert archive_res.status_code == 200
    assert archive_res.json()["status"] == "ARCHIVED"

    # 2. Gọi PATCH /publish để khôi phục
    publish_res = await client.patch(f"/api/v1/admin/articles/{art_id}/publish", headers=admin_headers)
    assert publish_res.status_code == 200
    assert publish_res.json()["status"] == "PUBLISHED"


@pytest.mark.asyncio
async def test_restore_article_api(client: AsyncClient, admin_headers: dict, db_session):
    # Tạo category
    category = Category(status="ACTIVE", is_visible=True, sort_order=1)
    db_session.add(category)
    await db_session.commit()
    test_category_ids.append(category.id)

    # Tạo article
    payload = {
        "category_id": str(category.id),
        "status": "PUBLISHED",
        "is_draft": False,
        "translations": {
            "vi": {
                "title": "Bài viết test restore",
                "slug": "bai-viet-test-restore",
                "content": "Nội dung"
            }
        }
    }
    res = await client.post("/api/v1/admin/articles", json=payload, headers=admin_headers)
    assert res.status_code == 201
    art_id = res.json()["id"]
    test_article_ids.append(art_id)

    # Xóa mềm bài viết qua API DELETE
    delete_res = await client.delete(f"/api/v1/admin/articles/{art_id}", headers=admin_headers)
    assert delete_res.status_code == 204

    # Khôi phục bài viết qua API POST /restore
    restore_res = await client.post(f"/api/v1/admin/articles/{art_id}/restore", headers=admin_headers)
    assert restore_res.status_code == 200

    # Lấy lại chi tiết bài viết (Admin) -> Mong đợi 200 (do đã được khôi phục thành công)
    get_res = await client.get(f"/api/v1/admin/articles/{art_id}", headers=admin_headers)
    assert get_res.status_code == 200
