import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserResponse
from app.modules.banner.models import BannerPosition
from app.modules.banner.schemas import (
    BannerCreate,
    BannerResponse,
    BannerStatusUpdate,
    BannerUpdate,
    BannerPaginationResponse,
)
from app.modules.banner.service import banner_service
from app.modules.audit.service import log_action

banners_router = APIRouter()

# ──────────────────────────────────────────────
# Public Portal APIs
# ──────────────────────────────────────────────

@banners_router.get("", response_model=list[BannerResponse])
async def list_banners_portal(
    position: Optional[BannerPosition] = Query(default=None, description="Lọc theo vị trí hiển thị"),
    db: AsyncSession = Depends(get_db),
) -> list[BannerResponse]:
    """
    Lấy danh sách các banner đang hiệu lực hiển thị ở Portal (Public - Không cần đăng nhập).
    Trả về mảng danh sách được sắp xếp theo sort_order tăng dần.
    """
    banners = await banner_service.list_banners_portal(db, position=position)
    return [BannerResponse.model_validate(b) for b in banners]


# ──────────────────────────────────────────────
# Admin Management APIs
# ──────────────────────────────────────────────

@banners_router.get("/admin", response_model=BannerPaginationResponse)
async def list_banners_admin(
    page: int = Query(default=1, ge=1, description="Chỉ số trang (bắt đầu từ 1)"),
    page_size: int = Query(default=10, ge=1, le=1000, description="Số lượng banner trên mỗi trang"),
    search: Optional[str] = Query(default=None, description="Tìm kiếm theo tiêu đề hoặc mô tả"),
    position: Optional[BannerPosition] = Query(default=None, description="Lọc theo vị trí hiển thị"),
    is_active: Optional[bool] = Query(default=None, description="Lọc theo trạng thái hoạt động"),
    sort_by: str = Query(default="sort_order", description="Trường sắp xếp (title, sort_order, created_at)"),
    order: str = Query(default="asc", description="Hướng sắp xếp (asc, desc)"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BannerPaginationResponse:
    """
    Lấy danh sách các banner phân trang phục vụ quản lý (Yêu cầu đăng nhập).
    """
    # Validation sort_by
    allowed_sort_fields = {"title", "sort_order", "created_at"}
    if sort_by not in allowed_sort_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Trường sắp xếp 'sort_by' không hợp lệ. Cho phép: {', '.join(allowed_sort_fields)}"
        )

    # Validation order
    if order.lower() not in {"asc", "desc"}:
        raise HTTPException(
            status_code=400,
            detail="Hướng sắp xếp 'order' chỉ được phép là 'asc' hoặc 'desc'"
        )

    banners, total = await banner_service.list_banners_admin(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        position=position,
        is_active=is_active,
        sort_by=sort_by,
        order=order,
    )

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return BannerPaginationResponse(
        items=[BannerResponse.model_validate(b) for b in banners],
        page=page,
        page_size=page_size,
        total_items=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
    )


@banners_router.get("/{banner_id}", response_model=BannerResponse)
async def get_banner(
    banner_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> BannerResponse:
    """
    Lấy chi tiết thông tin một banner theo ID.
    """
    banner = await banner_service.get_banner_by_id(db, banner_id)
    return BannerResponse.model_validate(banner)


@banners_router.post("", response_model=BannerResponse, status_code=201)
async def create_banner(
    request: Request,
    payload: BannerCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BannerResponse:
    """
    Tạo mới một banner hiển thị.
    """
    banner = await banner_service.create_banner(db, payload)
    
    # Audit log
    await log_action(
        db,
        current_user,
        "BANNER_CREATED",
        "banner",
        banner.id,
        payload.model_dump(),
        request,
    )
    await db.commit()
    return BannerResponse.model_validate(banner)


@banners_router.put("/{banner_id}", response_model=BannerResponse)
async def update_banner(
    request: Request,
    banner_id: uuid.UUID,
    payload: BannerUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BannerResponse:
    """
    Cập nhật thông tin chi tiết một banner.
    """
    banner = await banner_service.update_banner(db, banner_id, payload)

    # Audit log
    await log_action(
        db,
        current_user,
        "BANNER_UPDATED",
        "banner",
        banner.id,
        payload.model_dump(exclude_unset=True),
        request,
    )
    await db.commit()
    return BannerResponse.model_validate(banner)


@banners_router.patch("/{banner_id}/status", response_model=BannerResponse)
async def update_banner_status(
    request: Request,
    banner_id: uuid.UUID,
    payload: BannerStatusUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BannerResponse:
    """
    Cập nhật nhanh trạng thái hoạt động (bật/tắt) của banner.
    """
    banner = await banner_service.update_banner_status(db, banner_id, payload.is_active)

    # Audit log
    await log_action(
        db,
        current_user,
        "BANNER_STATUS_UPDATED",
        "banner",
        banner.id,
        {"is_active": payload.is_active},
        request,
    )
    await db.commit()
    return BannerResponse.model_validate(banner)


@banners_router.delete("/{banner_id}", status_code=204)
async def delete_banner(
    request: Request,
    banner_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Xóa mềm một banner và tự động dồn thứ tự.
    """
    await banner_service.delete_banner(db, banner_id)

    # Audit log
    await log_action(
        db,
        current_user,
        "BANNER_DELETED",
        "banner",
        banner_id,
        None,
        request,
    )
    await db.commit()
