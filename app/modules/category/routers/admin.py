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
    CategoryUpdate,
    CategorySlugCheckResponse,
    AdminCategoryResponse,
    AdminCategoryTreeNode,
)
from app.modules.category.service import category_service

admin_router = APIRouter()


@admin_router.get("", response_model=list[AdminCategoryResponse])
async def list_categories_admin(
    search: Optional[str] = None,
    status: Optional[str] = None,
    only_has_articles: bool = Query(default=False, description="Chỉ lấy danh mục có chứa ít nhất 1 bài viết"),
    db: AsyncSession = Depends(get_db),
) -> list[AdminCategoryResponse]:
    """
    [CMS Admin] Lấy danh sách tất cả các danh mục bài viết (phẳng).
    """
    categories = await category_service.list_categories(db, search=search, status=status, only_has_articles=only_has_articles)
    return [AdminCategoryResponse.model_validate(c) for c in categories]


@admin_router.get("/tree", response_model=list[AdminCategoryTreeNode])
async def get_category_tree_admin(
    with_article_count: bool = Query(default=False, description="Bật thống kê số lượng bài viết đã xuất bản"),
    only_has_articles: bool = Query(default=False, description="Chỉ lấy cây danh mục có chứa bài viết đã xuất bản"),
    db: AsyncSession = Depends(get_db),
) -> list[AdminCategoryTreeNode]:
    """
    [CMS Admin] Lấy cấu trúc cây danh mục bài viết đầy đủ cho trang quản trị.
    """
    tree = await category_service.get_category_tree(db, with_article_count=with_article_count, only_has_articles=only_has_articles, lang="vi")
    return [AdminCategoryTreeNode.model_validate(node) for node in tree]


@admin_router.get("/check-slug", response_model=CategorySlugCheckResponse)
async def check_category_slug_admin(
    slug: str,
    exclude_id: Optional[uuid.UUID] = None,
    lang: str = "vi",
    db: AsyncSession = Depends(get_db),
) -> CategorySlugCheckResponse:
    """
    [CMS Admin] Kiểm tra xem slug có trùng lặp không trong cùng ngôn ngữ.
    """
    result = await category_service.check_slug_uniqueness(db, slug, lang, exclude_id)
    return CategorySlugCheckResponse(**result)


@admin_router.get("/{category_id}", response_model=AdminCategoryResponse)
async def get_category_admin(
    category_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> AdminCategoryResponse:
    """
    [CMS Admin] Lấy thông tin chi tiết một danh mục theo ID đầy đủ bản dịch.
    """
    category = await category_service.get_category_by_id(db, category_id, lang="vi")
    return AdminCategoryResponse.model_validate(category)


@admin_router.post("", response_model=AdminCategoryResponse, status_code=201)
async def create_category_admin(
    request: Request,
    payload: CategoryCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AdminCategoryResponse:
    """
    [CMS Admin] Tạo mới danh mục.
    """
    category = await category_service.create_category(db, payload, current_user.id)
    await log_action(
        db, current_user, "CATEGORY_CREATED", "category", category.id,
        {"name": getattr(category, "name", ""), "slug": getattr(category, "slug", "")},
        request,
    )
    await db.commit()
    return AdminCategoryResponse.model_validate(category)


@admin_router.put("/reorder", status_code=200)
async def reorder_categories_admin(
    request: Request,
    payload: CategoryReorderRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    [CMS Admin] Cập nhật đồng loạt kéo thả cấu trúc cây danh mục.
    """
    await category_service.reorder_categories(db, payload, current_user.id)
    await log_action(
        db, current_user, "CATEGORIES_REORDERED", "category", None,
        {"items_count": len(payload.items)},
        request,
    )
    await db.commit()
    return {"success": True, "reordered": len(payload.items)}


@admin_router.put("/{category_id}", response_model=AdminCategoryResponse)
async def update_category_admin(
    request: Request,
    category_id: uuid.UUID,
    payload: CategoryUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AdminCategoryResponse:
    """
    [CMS Admin] Cập nhật chi tiết danh mục.
    """
    category = await category_service.update_category(db, category_id, payload, current_user.id)
    await log_action(
        db, current_user, "CATEGORY_UPDATED", "category", category.id,
        payload.model_dump(exclude_unset=True),
        request,
    )
    await db.commit()
    return AdminCategoryResponse.model_validate(category)


@admin_router.delete("/{category_id}", status_code=204)
async def delete_category_admin(
    request: Request,
    category_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    [CMS Admin] Xóa mềm danh mục.
    """
    await category_service.delete_category(db, category_id, current_user.id)
    await log_action(
        db, current_user, "CATEGORY_DELETED", "category", category_id, None, request
    )
    await db.commit()


@admin_router.post("/{category_id}/restore", response_model=AdminCategoryResponse)
async def restore_category_admin(
    request: Request,
    category_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AdminCategoryResponse:
    """
    [CMS Admin] Khôi phục danh mục đã bị xóa mềm.
    """
    category = await category_service.restore_category(db, category_id, current_user.id)
    await log_action(
        db, current_user, "CATEGORY_RESTORED", "category", category_id, None, request
    )
    await db.commit()
    return AdminCategoryResponse.model_validate(category)
