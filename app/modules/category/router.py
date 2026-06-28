import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.audit.service import log_action
from app.modules.auth.dependencies import has_permission
from app.modules.auth.schemas import UserResponse
from app.modules.category.schemas import (
    CategoryCreate,
    CategoryReorderRequest,
    CategoryResponse,
    CategoryTreeNode,
    CategoryUpdate,
)
from app.modules.category.service import category_service

category_router = APIRouter()


# ──────────────────────────────────────────────
# Category CRUD
# ──────────────────────────────────────────────

@category_router.get("", response_model=list[CategoryResponse])
async def list_categories(
    search: Optional[str] = None,
    status: Optional[str] = None,
    current_user: UserResponse = Depends(has_permission("category.view")),
    db: AsyncSession = Depends(get_db),
) -> list[CategoryResponse]:
    """
    Lấy danh sách tất cả các danh mục bài viết hoạt động.
    Hỗ trợ tìm kiếm theo tên và lọc theo trạng thái.
    Quyền yêu cầu: category.view
    """
    categories = await category_service.list_categories(db, search=search, status=status)
    return [CategoryResponse.model_validate(c) for c in categories]


@category_router.get("/tree", response_model=list[CategoryTreeNode])
async def get_category_tree(
    current_user: UserResponse = Depends(has_permission("category.view")),
    db: AsyncSession = Depends(get_db),
) -> list[CategoryTreeNode]:
    """
    Lấy cấu trúc cây danh mục bài viết hoàn chỉnh (Recursive tree).
    Phục vụ cho sơ đồ quản lý kéo thả hoặc bộ chọn phân cấp.
    Quyền yêu cầu: category.view
    """
    return await category_service.get_category_tree(db)


@category_router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: uuid.UUID,
    current_user: UserResponse = Depends(has_permission("category.view")),
    db: AsyncSession = Depends(get_db),
) -> CategoryResponse:
    """
    Lấy chi tiết thông tin danh mục theo ID.
    Quyền yêu cầu: category.view
    """
    category = await category_service.get_category_by_id(db, category_id)
    return CategoryResponse.model_validate(category)


@category_router.post("", response_model=CategoryResponse, status_code=201)
async def create_category(
    request: Request,
    payload: CategoryCreate,
    current_user: UserResponse = Depends(has_permission("category.create")),
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
    current_user: UserResponse = Depends(has_permission("category.update")),
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
    current_user: UserResponse = Depends(has_permission("category.update")),
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
    current_user: UserResponse = Depends(has_permission("category.delete")),
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
