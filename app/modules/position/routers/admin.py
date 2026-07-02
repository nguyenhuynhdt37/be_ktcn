import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.audit.service import log_action
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserResponse
from app.modules.position.schemas import (
    PositionCreate,
    AdminPositionResponse,
    PositionUpdate,
    PositionPaginationResponse,
    PositionStatsResponse,
)
from app.modules.position.service import position_service

admin_router = APIRouter()


@admin_router.get("", response_model=PositionPaginationResponse)
async def list_positions_admin(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=1000),
    search: Optional[str] = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
    sort_by: str = Query(default="sort_order"),
    order: str = Query(default="asc"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PositionPaginationResponse:
    """
    [CMS Admin] Lấy danh sách chức vụ có phân trang và translations.
    """
    positions, total = await position_service.list_positions(
        db=db,
        search=search,
        is_active=is_active,
        sort_by=sort_by,
        order=order,
        page=page,
        page_size=page_size,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return PositionPaginationResponse(
        items=[AdminPositionResponse.model_validate(p) for p in positions],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@admin_router.post("", response_model=AdminPositionResponse, status_code=201)
async def create_position_admin(
    request: Request,
    payload: PositionCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AdminPositionResponse:
    """
    [CMS Admin] Tạo chức vụ mới.
    """
    pos = await position_service.create_position(db, payload)
    await log_action(
        db, current_user, "POSITION_CREATED", "position", pos.id,
        {"name": pos.name}, request
    )
    await db.commit()
    return AdminPositionResponse.model_validate(pos)


@admin_router.get("/stats", response_model=PositionStatsResponse)
async def get_position_stats(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PositionStatsResponse:
    """
    [CMS Admin] Lấy thống kê số lượng chức vụ.
    """
    stats = await position_service.get_stats(db)
    return PositionStatsResponse.model_validate(stats)


@admin_router.get("/staffs-to-delete", response_model=list[dict])
async def get_staffs_to_delete(
    position_ids: str = Query(..., description="Danh sách ID chức vụ cách nhau bởi dấu phẩy"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    [CMS Admin] Lấy danh sách giảng viên đang đảm nhiệm các chức vụ này (để cảnh báo trước khi xóa).
    """
    from app.modules.staff.models import Staff
    from app.modules.department.models import DepartmentTranslation
    from app.modules.language.models import Language
    from sqlalchemy import select
    
    id_list = []
    for x in position_ids.split(","):
        if x.strip():
            try:
                id_list.append(uuid.UUID(x.strip()))
            except ValueError:
                continue
                
    if not id_list:
        return []

    # Lấy language id của tiếng Việt
    lang_stmt = select(Language.id).where(Language.code == "vi")
    lang_id = (await db.execute(lang_stmt)).scalar()
        
    stmt = (
        select(
            Staff.id,
            Staff.full_name,
            Staff.avatar_object_key,
            DepartmentTranslation.name,
            Staff.position_id
        )
        .outerjoin(DepartmentTranslation, (DepartmentTranslation.department_id == Staff.department_id) & (DepartmentTranslation.language_id == lang_id))
        .where(Staff.position_id.in_(id_list), Staff.deleted_at.is_(None))
    )
    res = await db.execute(stmt)
    rows = res.all()
    
    return [
        {
            "id": str(row[0]),
            "full_name": row[1],
            "avatar_object_key": row[2],
            "department_name": row[3] or "Bộ môn",
            "position_id": str(row[4])
        }
        for row in rows
    ]


@admin_router.get("/{position_id}", response_model=AdminPositionResponse)
async def get_position_admin(
    position_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AdminPositionResponse:
    """
    [CMS Admin] Chi tiết chức vụ.
    """
    pos = await position_service.get_position(db, position_id)
    return AdminPositionResponse.model_validate(pos)


@admin_router.put("/{position_id}", response_model=AdminPositionResponse)
async def update_position_admin(
    request: Request,
    position_id: uuid.UUID,
    payload: PositionUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AdminPositionResponse:
    """
    [CMS Admin] Cập nhật chức vụ.
    """
    pos = await position_service.update_position(db, position_id, payload)
    await log_action(
        db, current_user, "POSITION_UPDATED", "position", pos.id,
        {"name": pos.name}, request
    )
    await db.commit()
    return AdminPositionResponse.model_validate(pos)


@admin_router.delete("/{position_id}", status_code=204)
async def delete_position_admin(
    request: Request,
    position_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    [CMS Admin] Xóa chức vụ.
    """
    pos = await position_service.get_position(db, position_id)
    await position_service.delete_position(db, position_id)
    await log_action(
        db, current_user, "POSITION_DELETED", "position", position_id,
        {"name": pos.name}, request
    )
    await db.commit()
