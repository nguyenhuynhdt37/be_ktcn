import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.audit.service import log_action
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserResponse
from app.modules.category.schemas import (
    CategoryCreate,
    CategoryReorderRequest,
    CategoryResponse,
    CategoryTreeNode,
    CategoryUpdate,
    CategorySlugCheckResponse,
)
from app.modules.category.service import category_service
from app.modules.article.schemas import PortalArticlePaginationResponse, PortalArticleResponse
from app.modules.article.service import article_service

category_router = APIRouter()


# ──────────────────────────────────────────────
# Category CRUD
# ──────────────────────────────────────────────

@category_router.get("", response_model=list[CategoryResponse])
async def list_categories(
    search: Optional[str] = None,
    status: Optional[str] = None,
    only_has_articles: bool = Query(default=False, description="Chỉ lấy danh mục có chứa ít nhất 1 bài viết đã xuất bản"),
    db: AsyncSession = Depends(get_db),
) -> list[CategoryResponse]:
    """
    Lấy danh sách tất cả các danh mục bài viết hoạt động (Public API).
    Hỗ trợ tìm kiếm, lọc theo trạng thái và lọc danh mục có bài viết.
    """
    categories = await category_service.list_categories(db, search=search, status=status, only_has_articles=only_has_articles)
    return [CategoryResponse.model_validate(c) for c in categories]


@category_router.get("/tree", response_model=list[CategoryTreeNode])
async def get_category_tree(
    with_article_count: bool = Query(default=False, description="Bật thống kê số lượng bài viết đã xuất bản"),
    only_has_articles: bool = Query(default=False, description="Chỉ lấy cây danh mục có chứa bài viết đã xuất bản"),
    db: AsyncSession = Depends(get_db),
) -> list[CategoryTreeNode]:
    """
    Lấy cấu trúc cây danh mục bài viết hoàn chỉnh (Public API).
    Hỗ trợ bật thống kê bài viết và tự động cắt tỉa các danh mục trống.
    """
    return await category_service.get_category_tree(db, with_article_count=with_article_count, only_has_articles=only_has_articles)



@category_router.get("/check-slug", response_model=CategorySlugCheckResponse)
async def check_category_slug(
    slug: str,
    exclude_id: Optional[uuid.UUID] = None,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CategorySlugCheckResponse:
    """
    Kiểm tra xem slug có trùng lặp không.
    Nếu trùng, trả về exists=True và gợi ý slug mới có hậu tố tăng dần.
    Quyền yêu cầu: category.view
    """
    result = await category_service.check_slug_uniqueness(db, slug, exclude_id)
    return CategorySlugCheckResponse(**result)


@category_router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> CategoryResponse:
    """
    Lấy chi tiết thông tin danh mục theo ID (Public API).
    """
    category = await category_service.get_category_by_id(db, category_id)
    return CategoryResponse.model_validate(category)



@category_router.post("", response_model=CategoryResponse, status_code=201)
async def create_category(
    request: Request,
    payload: CategoryCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CategoryResponse:
    """
    Tạo danh mục mới. Tự sinh Slug và SEO meta nếu bỏ trống.
    Quyền yêu cầu: category.create
    """
    category = await category_service.create_category(db, payload, current_user.id)
    await log_action(
        db, current_user, "CATEGORY_CREATED", "category", category.id,
        {"name": payload.name, "slug": category.slug},
        request,
    )
    await db.commit()
    return CategoryResponse.model_validate(category)


# ──────────────────────────────────────────────
# Drag & Drop Reorder
# ──────────────────────────────────────────────

@category_router.put("/reorder", status_code=200)
async def reorder_categories(
    request: Request,
    payload: CategoryReorderRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Cập nhật đồng loạt vị trí kéo thả danh mục (parent_id và sort_order).
    Có kiểm tra vòng lặp toàn bộ batch trước khi lưu.
    Quyền yêu cầu: category.update
    """
    await category_service.reorder_categories(db, payload, current_user.id)
    await log_action(
        db, current_user, "CATEGORIES_REORDERED", "category", None,
        {"items_count": len(payload.items)},
        request,
    )
    await db.commit()
    return {"success": True, "reordered": len(payload.items)}


@category_router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    request: Request,
    category_id: uuid.UUID,
    payload: CategoryUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CategoryResponse:
    """
    Cập nhật thông tin chi tiết danh mục.
    Tự động kiểm tra liên kết vòng lặp và cập nhật tính duy nhất của slug.
    Quyền yêu cầu: category.update
    """
    category = await category_service.update_category(db, category_id, payload, current_user.id)
    await log_action(
        db, current_user, "CATEGORY_UPDATED", "category", category.id,
        payload.model_dump(exclude_unset=True),
        request,
    )
    await db.commit()
    return CategoryResponse.model_validate(category)


@category_router.delete("/{category_id}", status_code=204)
async def delete_category(
    request: Request,
    category_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Xóa mềm danh mục.
    Chặn xóa nếu danh mục này đang chứa danh mục con hoạt động hoặc có bài viết liên kết.
    Quyền yêu cầu: category.delete
    """
    await category_service.delete_category(db, category_id, current_user.id)
    await log_action(
        db, current_user, "CATEGORY_DELETED", "category", category_id, None, request
    )
    await db.commit()


@category_router.get("/{category_slug}/articles", response_model=PortalArticlePaginationResponse)
async def list_category_articles_portal(
    category_slug: str,
    page: int = Query(default=1, ge=1, description="Chỉ số trang (bắt đầu từ 1)"),
    page_size: int = Query(default=10, ge=1, le=100, alias="page_size", description="Số lượng bài viết trên mỗi trang"),
    db: AsyncSession = Depends(get_db),
) -> PortalArticlePaginationResponse:
    """
    Lấy danh sách các bài viết thuộc danh mục chỉ định qua slug cho Portal Client (Public API).
    Mặc định sắp xếp: bài ghim (is_pinned) lên đầu, sau đó đến ngày công bố (publish_at) giảm dần.
    """
    items, total = await article_service.list_articles_portal(
        db,
        category_slug=category_slug,
        page=page,
        page_size=page_size
    )

    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    has_next = page < total_pages
    has_previous = page > 1

    return PortalArticlePaginationResponse(
        items=[PortalArticleResponse.model_validate(item) for item in items],
        page=page,
        page_size=page_size,
        total_items=total,
        total_pages=total_pages,
        has_next=has_next,
        has_previous=has_previous,
    )
