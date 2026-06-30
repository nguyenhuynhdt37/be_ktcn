import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Request, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.audit.service import log_action
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserResponse
from app.modules.tag.schemas import TagCreate, TagResponse, TagStatusUpdate, TagUpdate
from app.modules.tag.service import tag_service
from app.shared.pagination import PaginatedResponse, PaginationParams

router = APIRouter()


@router.get("", response_model=PaginatedResponse[TagResponse])
async def list_tags(
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    only_has_articles: bool = Query(default=False, description="Chỉ lấy các tag có chứa ít nhất 1 bài viết đã xuất bản"),
    params: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[TagResponse]:
    """
    Lấy danh sách các Tag phân trang.
    Hỗ trợ tìm kiếm, lọc theo trạng thái và lọc các tag có bài viết.
    """
    tags, total = await tag_service.list_tags(
        db, search=search, is_active=is_active, only_has_articles=only_has_articles, page=params.page, limit=params.limit
    )
    # Cast to schema response items
    response_items = [TagResponse.model_validate(tag) for tag in tags]
    return PaginatedResponse.create(items=response_items, total=total, params=params)


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(
    tag_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TagResponse:
    """
    Lấy chi tiết Tag theo ID.
    """
    tag = await tag_service.get_tag_by_id(db, tag_id)
    return TagResponse.model_validate(tag)


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    request: Request,
    payload: TagCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TagResponse:
    """
    Tạo mới một Tag. Tự sinh slug unique nếu để trống.
    """
    tag = await tag_service.create_tag(db, payload)
    
    # Ghi nhận Audit Log
    await log_action(
        db,
        current_user,
        "TAG_CREATED",
        "tag",
        tag.id,
        {"name": tag.name, "slug": tag.slug},
        request,
    )
    await db.commit()
    return TagResponse.model_validate(tag)


@router.put("/{tag_id}", response_model=TagResponse)
async def update_tag(
    request: Request,
    tag_id: uuid.UUID,
    payload: TagUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TagResponse:
    """
    Cập nhật thông tin Tag theo ID.
    """
    tag = await tag_service.update_tag(db, tag_id, payload)
    
    # Ghi nhận Audit Log
    await log_action(
        db,
        current_user,
        "TAG_UPDATED",
        "tag",
        tag.id,
        {"name": tag.name, "slug": tag.slug},
        request,
    )
    await db.commit()
    return TagResponse.model_validate(tag)


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    request: Request,
    tag_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Xóa mềm một Tag theo ID.
    """
    tag = await tag_service.get_tag_by_id(db, tag_id)
    await tag_service.delete_tag(db, tag_id)
    
    # Ghi nhận Audit Log
    await log_action(
        db,
        current_user,
        "TAG_DELETED",
        "tag",
        tag_id,
        {"name": tag.name, "slug": tag.slug},
        request,
    )
    await db.commit()


@router.patch("/{tag_id}/status", response_model=TagResponse)
async def toggle_tag_status(
    request: Request,
    tag_id: uuid.UUID,
    payload: TagStatusUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TagResponse:
    """
    Bật/Tắt trạng thái hoạt động (is_active) của Tag.
    """
    tag = await tag_service.toggle_tag_status(db, tag_id, payload.is_active)
    
    # Ghi nhận Audit Log
    await log_action(
        db,
        current_user,
        "TAG_STATUS_TOGGLED",
        "tag",
        tag.id,
        {"name": tag.name, "is_active": tag.is_active},
        request,
    )
    await db.commit()
    return TagResponse.model_validate(tag)
