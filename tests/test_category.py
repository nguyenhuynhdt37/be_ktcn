import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select, delete
from datetime import datetime, UTC

from app.core.exceptions import BadRequestException, NotFoundException
from app.modules.category.models import Category, CategoryTranslation
from app.modules.language.models import Language
from app.modules.article.models import Article, ArticleStatus


# Lưu trữ danh sách IDs được tạo ra trong quá trình test để dọn dẹp chính xác, tránh xóa sạch DB
test_category_ids = []
test_article_ids = []

@pytest.fixture(autouse=True)
async def cleanup_data(db_session):
    """Tự động dọn dẹp các Category và Article tạo ra trong quá trình test bằng ID."""
    global test_category_ids, test_article_ids
    test_category_ids.clear()
    test_article_ids.clear()
    yield
    if test_article_ids:
        # Xóa các articles liên kết trước
        await db_session.execute(
            delete(Article).where(Article.id.in_(test_article_ids))
        )
    if test_category_ids:
        # Xóa các translations liên kết trước
        await db_session.execute(
            delete(CategoryTranslation).where(CategoryTranslation.category_id.in_(test_category_ids))
        )
        # Xóa categories
        await db_session.execute(
            delete(Category).where(Category.id.in_(test_category_ids))
        )
    await db_session.commit()
    test_category_ids.clear()
    test_article_ids.clear()



@pytest.mark.asyncio
async def test_create_category_api(client: AsyncClient, admin_headers: dict, db_session):
    """Test API POST /api/v1/categories tạo mới category đa ngôn ngữ thành công."""
    
    # 1. Chuẩn bị payload tạo mới category
    payload = {
        "parent_id": None,
        "status": "ACTIVE",
        "is_visible": True,
        "thumbnail_id": None,
        "is_weekly_schedule": True,
        "sort_order": 10,
        "translations": {
            "vi": {
                "name": "Tin học Đại cương",
                "slug": "tin-hoc-dai-cuong",
                "description": "Môn học cơ bản",
                "seo_title": "Tin học Đại cương SEO",
                "seo_description": "Mô tả SEO"
            },
            "en": {
                "name": "Introduction to IT",
                "slug": "introduction-to-it",
                "description": "Basic IT course",
                "seo_title": "Intro IT SEO",
                "seo_description": "Intro IT SEO Desc"
            }
        }
    }
    
    # 2. Gửi request POST
    res = await client.post("/api/v1/admin/categories", json=payload, headers=admin_headers)
    assert res.status_code == 201
    data = res.json()
    
    # 3. Assert response fields
    assert "id" in data
    test_category_ids.append(data["id"])
    assert data["status"] == "ACTIVE"
    assert data["sort_order"] == 10
    assert data["is_weekly_schedule"] is True
    
    # 4. Assert translations response
    assert "translations" in data
    assert "vi" in data["translations"]
    assert "en" in data["translations"]
    assert data["translations"]["vi"]["name"] == "Tin học Đại cương"
    assert data["translations"]["en"]["name"] == "Introduction to IT"
    
    # Assert is_translated
    assert "is_translated" in data
    assert data["is_translated"]["vi"] is True
    assert data["is_translated"]["en"] is True
    assert data["translations"]["vi"]["is_translated"] is True
    assert data["translations"]["en"]["is_translated"] is True


@pytest.mark.asyncio
async def test_update_category_api(client: AsyncClient, admin_headers: dict, db_session):
    """Test API PUT /api/v1/categories/{id} cập nhật category thành công."""
    
    # 1. Tạo trước một Category và bản dịch tiếng Việt bằng API hoặc DB trực tiếp
    # Để đơn giản, ta gọi POST để tạo trước
    payload_create = {
        "parent_id": None,
        "status": "ACTIVE",
        "is_visible": True,
        "thumbnail_id": None,
        "is_weekly_schedule": False,
        "sort_order": 0,
        "translations": {
            "vi": {
                "name": "Thể dục",
                "slug": "the-duc",
                "description": "Môn thể dục",
                "seo_title": "Thể dục SEO",
                "seo_description": "Thể dục SEO Desc"
            }
        }
    }
    create_res = await client.post("/api/v1/admin/categories", json=payload_create, headers=admin_headers)
    assert create_res.status_code == 201
    category_id = create_res.json()["id"]
    test_category_ids.append(category_id)
    
    # 2. Chuẩn bị payload cập nhật
    payload_update = {
        "sort_order": 20,
        "translations": {
            "vi": {
                "name": "Thể dục quốc phòng",
                "slug": "the-duc-quoc-phong",
                "description": "Môn thể dục mới"
            },
            "en": {
                "name": "Physical Education",
                "slug": "physical-education",
                "description": "PE course"
            }
        }
    }
    
    # 3. Gửi request PUT
    update_res = await client.put(f"/api/v1/admin/categories/{category_id}", json=payload_update, headers=admin_headers)
    assert update_res.status_code == 200
    updated_data = update_res.json()
    
    # 4. Assert updated data
    assert updated_data["sort_order"] == 20
    assert updated_data["translations"]["vi"]["name"] == "Thể dục quốc phòng"
    assert updated_data["translations"]["vi"]["slug"] == "the-duc-quoc-phong"
    assert updated_data["translations"]["en"]["name"] == "Physical Education"
    assert updated_data["translations"]["en"]["slug"] == "physical-education"


@pytest.mark.asyncio
async def test_delete_category_constraint_active_articles(client: AsyncClient, admin_headers: dict, db_session):
    """Test không cho phép xóa danh mục khi vẫn còn ít nhất một bài viết hoạt động."""
    # 1. Tạo Category
    payload = {
        "parent_id": None,
        "status": "ACTIVE",
        "translations": {
            "vi": {
                "name": "Danh mục test xóa",
                "slug": "danh-muc-test-xoa",
                "description": "Danh mục để test ràng buộc xóa"
            }
        }
    }
    create_res = await client.post("/api/v1/admin/categories", json=payload, headers=admin_headers)
    assert create_res.status_code == 201
    category_id = create_res.json()["id"]
    test_category_ids.append(category_id)

    # 2. Tạo một bài viết thuộc Category này
    article = Article(
        title="Bài viết test xóa category",
        slug="bai-viet-test-xoa-category",
        content="Nội dung bài viết test",
        category_id=uuid.UUID(category_id)
    )
    db_session.add(article)
    await db_session.commit()
    test_article_ids.append(article.id)

    # 3. Thử gọi API xóa Category -> Mong đợi lỗi 400
    delete_res = await client.delete(f"/api/v1/admin/categories/{category_id}", headers=admin_headers)
    assert delete_res.status_code == 400
    error_data = delete_res.json()
    assert error_data["error"]["code"] == "CATEGORY_HAS_ACTIVE_ARTICLES"
    assert "Không thể xóa danh mục đang có bài viết hoạt động" in error_data["error"]["message"]


@pytest.mark.asyncio
async def test_delete_category_with_soft_deleted_articles(client: AsyncClient, admin_headers: dict, db_session):
    """Test cho phép xóa danh mục nếu tất cả bài viết liên kết đã bị xóa mềm."""
    # 1. Tạo Category
    payload = {
        "parent_id": None,
        "status": "ACTIVE",
        "translations": {
            "vi": {
                "name": "Danh mục test xóa soft delete",
                "slug": "danh-muc-test-xoa-soft-delete",
                "description": "Danh mục để test ràng buộc xóa khi bài viết bị soft delete"
            }
        }
    }
    create_res = await client.post("/api/v1/admin/categories", json=payload, headers=admin_headers)
    assert create_res.status_code == 201
    category_id = create_res.json()["id"]
    test_category_ids.append(category_id)

    # 2. Tạo một bài viết đã bị xóa mềm thuộc Category này
    article = Article(
        title="Bài viết bị xóa mềm",
        slug="bai-viet-bi-xoa-mem",
        content="Nội dung bài viết bị xóa mềm",
        category_id=uuid.UUID(category_id),
        deleted_at=datetime.now(UTC)
    )
    db_session.add(article)
    await db_session.commit()
    test_article_ids.append(article.id)

    # 3. Gọi API xóa Category -> Mong đợi xóa thành công (204)
    delete_res = await client.delete(f"/api/v1/admin/categories/{category_id}", headers=admin_headers)
    assert delete_res.status_code == 204


@pytest.mark.asyncio
async def test_category_article_count_calculation(client: AsyncClient, admin_headers: dict, db_session):
    """Test thống kê article_count đúng đắn trong API List, Detail và Tree."""
    # 1. Tạo Category
    payload = {
        "parent_id": None,
        "status": "ACTIVE",
        "translations": {
            "vi": {
                "name": "Danh mục đếm bài viết",
                "slug": "danh-muc-dem-bai-viet",
                "description": "Danh mục test đếm bài viết"
            }
        }
    }
    create_res = await client.post("/api/v1/admin/categories", json=payload, headers=admin_headers)
    assert create_res.status_code == 201
    category_id = create_res.json()["id"]
    test_category_ids.append(category_id)

    # 2. Tạo 2 bài viết hoạt động và 1 bài viết bị xóa mềm
    article_published = Article(
        title="Bài viết đã xuất bản",
        slug="bai-viet-da-xuat-ban",
        content="Content published",
        category_id=uuid.UUID(category_id),
        status=ArticleStatus.PUBLISHED,
        is_draft=False
    )
    article_draft = Article(
        title="Bài viết nháp",
        slug="bai-viet-nhap",
        content="Content draft",
        category_id=uuid.UUID(category_id),
        status=ArticleStatus.DRAFT,
        is_draft=True
    )
    article_deleted = Article(
        title="Bài viết đã bị xóa mềm",
        slug="bai-viet-da-bi-xoa-mem",
        content="Content deleted",
        category_id=uuid.UUID(category_id),
        deleted_at=datetime.now(UTC)
    )
    db_session.add_all([article_published, article_draft, article_deleted])
    await db_session.commit()
    test_article_ids.extend([article_published.id, article_draft.id, article_deleted.id])

    # 3. Kiểm tra API Chi tiết (Detail) -> article_count phải bằng 2
    detail_res = await client.get(f"/api/v1/admin/categories/{category_id}", headers=admin_headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["article_count"] == 2

    # 4. Kiểm tra API Danh sách (List) -> article_count phải bằng 2
    list_res = await client.get("/api/v1/admin/categories", headers=admin_headers)
    assert list_res.status_code == 200
    categories = list_res.json()
    target_category = next((c for c in categories if c["id"] == category_id), None)
    assert target_category is not None
    assert target_category["article_count"] == 2

    # 5. Kiểm tra API Cây (Tree) -> article_count phải bằng 2
    tree_res = await client.get("/api/v1/admin/categories/tree", headers=admin_headers)
    assert tree_res.status_code == 200
    tree_nodes = tree_res.json()
    target_node = next((n for n in tree_nodes if n["id"] == category_id), None)
    assert target_node is not None
    assert target_node["article_count"] == 2


@pytest.mark.asyncio
async def test_restore_category_api(client: AsyncClient, admin_headers: dict, db_session):
    """Test API POST /api/v1/categories/{id}/restore khôi phục category và đồng bộ lại bài viết."""
    # 1. Tạo Category
    payload = {
        "parent_id": None,
        "status": "ACTIVE",
        "translations": {
            "vi": {
                "name": "Danh mục test restore",
                "slug": "danh-muc-test-restore",
                "description": "Danh mục để test khôi phục"
            }
        }
    }
    create_res = await client.post("/api/v1/admin/categories", json=payload, headers=admin_headers)
    assert create_res.status_code == 201
    category_id = create_res.json()["id"]
    test_category_ids.append(category_id)

    # 2. Tạo một bài viết đã bị xóa mềm thuộc Category này
    article = Article(
        title="Bài viết bị xóa mềm khi test restore",
        slug="bai-viet-bi-xoa-mem-khi-test-restore",
        content="Nội dung bài viết",
        category_id=uuid.UUID(category_id),
        deleted_at=datetime.now(UTC)
    )
    db_session.add(article)
    await db_session.commit()
    test_article_ids.append(article.id)

    # 3. Xóa mềm Category (vì bài viết đã bị xóa mềm nên cho phép xóa Category)
    delete_res = await client.delete(f"/api/v1/admin/categories/{category_id}", headers=admin_headers)
    assert delete_res.status_code == 204

    # 4. Xác nhận Category đã bị xóa mềm bằng cách gọi API Chi tiết -> trả về 404
    detail_res = await client.get(f"/api/v1/admin/categories/{category_id}", headers=admin_headers)
    assert detail_res.status_code == 404

    # 5. Gọi API Khôi phục (Restore) -> trả về 200
    restore_res = await client.post(f"/api/v1/admin/categories/{category_id}/restore", headers=admin_headers)
    assert restore_res.status_code == 200
    data = restore_res.json()
    assert data["id"] == category_id
    assert data["article_count"] == 0  # Vì bài viết vẫn đang bị xóa mềm

    # 6. Khôi phục bài viết (set deleted_at = None) và kiểm tra xem danh mục có tự động đồng bộ đếm lại không
    stmt = select(Article).where(Article.id == article.id)
    art_res = await db_session.execute(stmt)
    db_article = art_res.scalar_one()
    db_article.deleted_at = None
    db_session.add(db_article)
    await db_session.commit()

    # Gọi lại API Chi tiết danh mục -> article_count phải bằng 1
    detail_res_again = await client.get(f"/api/v1/admin/categories/{category_id}", headers=admin_headers)
    assert detail_res_again.status_code == 200
    assert detail_res_again.json()["article_count"] == 1


@pytest.mark.asyncio
async def test_portal_category_api(client: AsyncClient, admin_headers: dict):
    """Test các API của Portal Category (/api/v1/portal/categories) hoạt động đúng thiết kế phẳng và làm sạch translations."""
    
    # 1. Tạo một category mẫu qua Admin API
    payload = {
        "parent_id": None,
        "status": "ACTIVE",
        "is_visible": True,
        "thumbnail_id": None,
        "is_weekly_schedule": False,
        "sort_order": 10,
        "translations": {
            "vi": {
                "name": "Mạng Máy Tính",
                "slug": "mang-may-tinh",
                "description": "Môn học mạng"
            },
            "en": {
                "name": "Computer Networks",
                "slug": "computer-networks",
                "description": "Network course"
            }
        }
    }
    
    res_create = await client.post("/api/v1/admin/categories", json=payload, headers=admin_headers)
    assert res_create.status_code == 201
    category_id = res_create.json()["id"]
    test_category_ids.append(uuid.UUID(category_id))
    
    # 2. Gọi Portal API Detail bằng tiếng Anh (?lang=en)
    res_portal_en = await client.get(f"/api/v1/portal/categories/{category_id}?lang=en")
    assert res_portal_en.status_code == 200
    data_en = res_portal_en.json()
    assert data_en["name"] == "Computer Networks"
    assert data_en["slug"].startswith("computer-networks")
    assert "translations" not in data_en
    assert "is_translated" not in data_en
    assert "status" not in data_en  # Không expose trường nội bộ
    
    # 3. Gọi Portal API Detail mặc định (Không truyền lang)
    res_portal_default = await client.get(f"/api/v1/portal/categories/{category_id}")
    assert res_portal_default.status_code == 200
    data_def = res_portal_default.json()
    assert data_def["name"] == "Mạng Máy Tính"
    assert "translations" not in data_def
    assert "status" not in data_def
    
    # 4. Gọi Portal API Tree
    res_tree = await client.get("/api/v1/portal/categories/tree?lang=en")
    assert res_tree.status_code == 200
    tree_data = res_tree.json()
    assert len(tree_data) > 0
    # Tìm node vừa tạo
    target_node = next((n for n in tree_data if n["id"] == category_id), None)
    assert target_node is not None
    assert target_node["name"] == "Computer Networks"
    assert "translations" not in target_node
    assert "status" not in target_node



