import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Request, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.audit.service import log_action
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserResponse
from app.modules.department.schemas import (
    DepartmentCreate,
    AdminDepartmentResponse,
    DepartmentUpdate,
    DepartmentPaginationResponse,
    DepartmentStatsResponse,
)
from app.modules.department.service import department_service

admin_router = APIRouter()


@admin_router.get("", response_model=DepartmentPaginationResponse)
async def list_departments_admin(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=1000),
    search: Optional[str] = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
    sort_by: str = Query(default="sort_order"),
    order: str = Query(default="asc"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DepartmentPaginationResponse:
    """
    [CMS Admin] Lấy danh sách bộ môn có phân trang và translations.
    """
    departments, total = await department_service.list_departments(
        db=db,
        search=search,
        is_active=is_active,
        sort_by=sort_by,
        order=order,
        page=page,
        page_size=page_size,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return DepartmentPaginationResponse(
        items=[AdminDepartmentResponse.model_validate(d) for d in departments],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@admin_router.post("", response_model=AdminDepartmentResponse, status_code=201)
async def create_department_admin(
    request: Request,
    payload: DepartmentCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AdminDepartmentResponse:
    """
    [CMS Admin] Tạo bộ môn mới.
    """
    dept = await department_service.create_department(db, payload)
    await log_action(
        db, current_user, "DEPARTMENT_CREATED", "department", dept.id,
        {"name": dept.name}, request
    )
    await db.commit()
    return AdminDepartmentResponse.model_validate(dept)


@admin_router.get("/stats", response_model=DepartmentStatsResponse)
async def get_department_stats(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DepartmentStatsResponse:
    """
    [CMS Admin] Lấy thống kê số lượng bộ môn.
    """
    stats = await department_service.get_stats(db)
    return DepartmentStatsResponse.model_validate(stats)


@admin_router.get("/staffs-to-delete", response_model=list[dict])
async def get_staffs_to_delete(
    department_ids: str = Query(..., description="Danh sách ID bộ môn cách nhau bởi dấu phẩy"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    [CMS Admin] Lấy danh sách giảng viên sẽ bị xóa liên đới khi xóa bộ môn.
    """
    from app.modules.staff.models import Staff
    from app.modules.position.models import PositionTranslation
    from app.modules.language.models import Language
    from sqlalchemy import select
    
    id_list = []
    for x in department_ids.split(","):
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
            PositionTranslation.name,
            Staff.department_id
        )
        .outerjoin(PositionTranslation, (PositionTranslation.position_id == Staff.position_id) & (PositionTranslation.language_id == lang_id))
        .where(Staff.department_id.in_(id_list), Staff.deleted_at.is_(None))
    )
    res = await db.execute(stmt)
    rows = res.all()
    
    return [
        {
            "id": str(row[0]),
            "full_name": row[1],
            "avatar_object_key": row[2],
            "position_name": row[3] or "Giảng viên",
            "department_id": str(row[4])
        }
        for row in rows
    ]


@admin_router.get("/{department_id}", response_model=AdminDepartmentResponse)
async def get_department_admin(
    department_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AdminDepartmentResponse:
    """
    [CMS Admin] Chi tiết bộ môn.
    """
    dept = await department_service.get_department(db, department_id)
    return AdminDepartmentResponse.model_validate(dept)


@admin_router.put("/{department_id}", response_model=AdminDepartmentResponse)
async def update_department_admin(
    request: Request,
    department_id: uuid.UUID,
    payload: DepartmentUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AdminDepartmentResponse:
    """
    [CMS Admin] Cập nhật bộ môn.
    """
    dept = await department_service.update_department(db, department_id, payload)
    await log_action(
        db, current_user, "DEPARTMENT_UPDATED", "department", dept.id,
        {"name": dept.name}, request
    )
    await db.commit()
    return AdminDepartmentResponse.model_validate(dept)


@admin_router.delete("/{department_id}", status_code=204)
async def delete_department_admin(
    request: Request,
    department_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    [CMS Admin] Xóa bộ môn.
    """
    dept = await department_service.get_department(db, department_id)
    await department_service.delete_department(db, department_id)
    await log_action(
        db, current_user, "DEPARTMENT_DELETED", "department", department_id,
        {"name": dept.name}, request
    )
    await db.commit()
