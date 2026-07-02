import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.audit.service import log_action
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserResponse
from app.modules.staff.schemas import (
    StaffCreate,
    AdminStaffResponse,
    StaffUpdate,
    StaffPaginationResponse,
    FacultyStaffStatsResponse,
)
from app.modules.staff.service import staff_service

admin_router = APIRouter()


@admin_router.get("", response_model=StaffPaginationResponse)
async def list_staffs_admin(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=1000),
    search: Optional[str] = Query(default=None),
    department_id: Optional[uuid.UUID] = Query(default=None),
    position_id: Optional[uuid.UUID] = Query(default=None),
    academic_title_id: Optional[uuid.UUID] = Query(default=None),
    degree_id: Optional[uuid.UUID] = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
    sort_by: str = Query(default="sort_order"),
    order: str = Query(default="asc"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StaffPaginationResponse:
    """
    [CMS Admin] Lấy danh sách giảng viên có phân trang, translations và load quan hệ.
    """
    staffs, total = await staff_service.list_staffs(
        db=db,
        search=search,
        department_id=department_id,
        position_id=position_id,
        academic_title_id=academic_title_id,
        degree_id=degree_id,
        is_active=is_active,
        sort_by=sort_by,
        order=order,
        page=page,
        page_size=page_size,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return StaffPaginationResponse(
        items=[AdminStaffResponse.model_validate(s) for s in staffs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@admin_router.post("", response_model=AdminStaffResponse, status_code=201)
async def create_staff_admin(
    request: Request,
    payload: StaffCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AdminStaffResponse:
    """
    [CMS Admin] Tạo hồ sơ giảng viên mới.
    """
    staff = await staff_service.create_staff(db, payload)
    await log_action(
        db, current_user, "STAFF_CREATED", "staff", staff.id,
        {"full_name": staff.full_name}, request
    )
    await db.commit()
    return AdminStaffResponse.model_validate(staff)


@admin_router.get("/stats", response_model=FacultyStaffStatsResponse)
async def get_faculty_staff_stats(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FacultyStaffStatsResponse:
    """
    [CMS Admin] Lấy thống kê số lượng bộ môn, chức vụ và giảng viên.
    """
    stats = await staff_service.get_stats(db)
    return FacultyStaffStatsResponse.model_validate(stats)


@admin_router.get("/{staff_id}", response_model=AdminStaffResponse)
async def get_staff_admin(
    staff_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AdminStaffResponse:
    """
    [CMS Admin] Chi tiết hồ sơ giảng viên.
    """
    staff = await staff_service.get_staff(db, staff_id)
    return AdminStaffResponse.model_validate(staff)


@admin_router.put("/{staff_id}", response_model=AdminStaffResponse)
async def update_staff_admin(
    request: Request,
    staff_id: uuid.UUID,
    payload: StaffUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AdminStaffResponse:
    """
    [CMS Admin] Cập nhật hồ sơ giảng viên.
    """
    staff = await staff_service.update_staff(db, staff_id, payload)
    await log_action(
        db, current_user, "STAFF_UPDATED", "staff", staff.id,
        {"full_name": staff.full_name}, request
    )
    await db.commit()
    return AdminStaffResponse.model_validate(staff)


@admin_router.delete("/{staff_id}", status_code=204)
async def delete_staff_admin(
    request: Request,
    staff_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    [CMS Admin] Xóa hồ sơ giảng viên.
    """
    staff = await staff_service.get_staff(db, staff_id)
    await staff_service.delete_staff(db, staff_id)
    await log_action(
        db, current_user, "STAFF_DELETED", "staff", staff_id,
        {"full_name": staff.full_name}, request
    )
    await db.commit()
