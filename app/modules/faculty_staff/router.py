import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Request, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.audit.service import log_action
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserResponse
from app.modules.faculty_staff.schemas import (
    PositionCreate,
    PositionResponse,
    PositionStatusUpdate,
    PositionUpdate,
    DepartmentCreate,
    DepartmentResponse,
    DepartmentStatusUpdate,
    DepartmentUpdate,
    StaffCreate,
    StaffResponse,
    StaffStatusUpdate,
    StaffUpdate,
    StaffPaginationResponse,
    PositionPaginationResponse,
    DepartmentPaginationResponse,
    DepartmentStatsResponse,
    PositionStatsResponse,
    StaffStatsResponse,
)
from app.modules.faculty_staff.service import position_service, department_service, staff_service


positions_router = APIRouter()


# ──────────────────────────────────────────────
# Position CRUD APIs
# ──────────────────────────────────────────────

@positions_router.get("", response_model=PositionPaginationResponse)
async def list_positions(
    page: int = Query(default=1, ge=1, description="Chỉ số trang (bắt đầu từ 1)"),
    page_size: int = Query(default=10, ge=1, le=1000, description="Số lượng chức vụ trên mỗi trang"),
    search: Optional[str] = Query(default=None, description="Tìm kiếm theo tên hoặc tên tiếng Anh"),
    is_active: Optional[bool] = Query(default=None, description="Lọc theo trạng thái hoạt động"),
    sort_by: str = Query(default="sort_order", description="Trường sắp xếp (name, sort_order, created_at)"),
    order: str = Query(default="asc", description="Hướng sắp xếp (asc, desc)"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PositionPaginationResponse:
    """
    Lấy danh sách tất cả các chức vụ với phân trang, lọc nâng cao và sắp xếp động.
    """
    # Validation sort_by
    allowed_sort_fields = {"name", "sort_order", "created_at"}
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
        items=[PositionResponse.model_validate(p) for p in positions],
        page=page,
        page_size=page_size,
        total_items=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
    )



@positions_router.get("/stats", response_model=PositionStatsResponse)
async def get_positions_stats(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PositionStatsResponse:
    """
    Lấy số liệu thống kê tổng quan về các chức vụ.
    Yêu cầu quyền Admin/Manager (phải đăng nhập).
    """
    stats = await position_service.get_stats(db)
    return PositionStatsResponse.model_validate(stats)


@positions_router.get("/{position_id}", response_model=PositionResponse)
async def get_position(
    position_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PositionResponse:
    """
    Lấy chi tiết thông tin một chức vụ theo ID.
    """
    pos = await position_service.get_position_by_id(db, position_id)
    return PositionResponse.model_validate(pos)


@positions_router.post("", response_model=PositionResponse, status_code=201)
async def create_position(
    request: Request,
    payload: PositionCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PositionResponse:
    """
    Tạo chức vụ giảng viên mới. Chặn trùng tên hoạt động.
    """
    pos = await position_service.create_position(db, payload)
    await log_action(
        db,
        current_user,
        "POSITION_CREATED",
        "position",
        pos.id,
        {"name": pos.name},
        request,
    )
    await db.commit()
    return PositionResponse.model_validate(pos)


@positions_router.put("/{position_id}", response_model=PositionResponse)
async def update_position(
    request: Request,
    position_id: uuid.UUID,
    payload: PositionUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PositionResponse:
    """
    Cập nhật thông tin chi tiết một chức vụ. Kiểm tra trùng tên khi đổi tên.
    """
    pos = await position_service.update_position(db, position_id, payload)
    await log_action(
        db,
        current_user,
        "POSITION_UPDATED",
        "position",
        pos.id,
        payload.model_dump(exclude_unset=True),
        request,
    )
    await db.commit()
    return PositionResponse.model_validate(pos)


@positions_router.patch("/{position_id}/status", response_model=PositionResponse)
async def update_position_status(
    request: Request,
    position_id: uuid.UUID,
    payload: PositionStatusUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PositionResponse:
    """
    Cập nhật nhanh trạng thái hoạt động (bật/tắt) của chức vụ.
    """
    pos = await position_service.update_position_status(db, position_id, payload.is_active)
    await log_action(
        db,
        current_user,
        "POSITION_STATUS_UPDATED",
        "position",
        pos.id,
        {"is_active": payload.is_active},
        request,
    )
    await db.commit()
    return PositionResponse.model_validate(pos)


@positions_router.delete("/{position_id}", status_code=204)
async def delete_position(
    request: Request,
    position_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Xóa mềm một chức vụ. Chặn xóa nếu vẫn còn giảng viên hoạt động liên kết.
    """
    await position_service.delete_position(db, position_id)
    await log_action(
        db,
        current_user,
        "POSITION_DELETED",
        "position",
        position_id,
        None,
        request,
    )
    await db.commit()


departments_router = APIRouter()


# ──────────────────────────────────────────────
# Department CRUD APIs
# ──────────────────────────────────────────────

@departments_router.get("", response_model=DepartmentPaginationResponse)
async def list_departments(
    page: int = Query(default=1, ge=1, description="Chỉ số trang (bắt đầu từ 1)"),
    page_size: int = Query(default=10, ge=1, le=1000, description="Số lượng bộ môn trên mỗi trang"),
    search: Optional[str] = Query(default=None, description="Tìm kiếm theo tên hoặc tên tiếng Anh"),
    is_active: Optional[bool] = Query(default=None, description="Lọc theo trạng thái hoạt động"),
    sort_by: str = Query(default="sort_order", description="Trường sắp xếp (name, sort_order, created_at)"),
    order: str = Query(default="asc", description="Hướng sắp xếp (asc, desc)"),
    db: AsyncSession = Depends(get_db),
) -> DepartmentPaginationResponse:
    """
    Lấy danh sách tất cả các bộ môn với phân trang, lọc nâng cao và sắp xếp động.
    """
    # Validation sort_by
    allowed_sort_fields = {"name", "sort_order", "created_at"}
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
        items=[DepartmentResponse.model_validate(d) for d in departments],
        page=page,
        page_size=page_size,
        total_items=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
    )



@departments_router.get("/stats", response_model=DepartmentStatsResponse)
async def get_departments_stats(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DepartmentStatsResponse:
    """
    Lấy số liệu thống kê tổng quan về các bộ môn.
    Yêu cầu quyền Admin/Manager (phải đăng nhập).
    """
    stats = await department_service.get_stats(db)
    return DepartmentStatsResponse.model_validate(stats)


@departments_router.get("/{department_id}", response_model=DepartmentResponse)
async def get_department(
    department_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> DepartmentResponse:
    """
    Lấy chi tiết thông tin một bộ môn theo ID.
    """
    dept = await department_service.get_department_by_id(db, department_id)
    return DepartmentResponse.model_validate(dept)


@departments_router.post("", response_model=DepartmentResponse, status_code=201)
async def create_department(
    request: Request,
    payload: DepartmentCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DepartmentResponse:
    """
    Tạo bộ môn giảng viên mới. Chặn trùng tên hoạt động, tự động tạo slug.
    """
    dept = await department_service.create_department(db, payload)
    await log_action(
        db,
        current_user,
        "DEPARTMENT_CREATED",
        "department",
        dept.id,
        {"name": dept.name},
        request,
    )
    await db.commit()
    return DepartmentResponse.model_validate(dept)


@departments_router.put("/{department_id}", response_model=DepartmentResponse)
async def update_department(
    request: Request,
    department_id: uuid.UUID,
    payload: DepartmentUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DepartmentResponse:
    """
    Cập nhật thông tin chi tiết một bộ môn. Kiểm tra trùng tên/slug khi đổi tên.
    """
    dept = await department_service.update_department(db, department_id, payload)
    await log_action(
        db,
        current_user,
        "DEPARTMENT_UPDATED",
        "department",
        dept.id,
        payload.model_dump(exclude_unset=True),
        request,
    )
    await db.commit()
    return DepartmentResponse.model_validate(dept)


@departments_router.patch("/{department_id}/status", response_model=DepartmentResponse)
async def update_department_status(
    request: Request,
    department_id: uuid.UUID,
    payload: DepartmentStatusUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DepartmentResponse:
    """
    Cập nhật nhanh trạng thái hoạt động (bật/tắt) của bộ môn.
    """
    dept = await department_service.update_department_status(db, department_id, payload.is_active)
    await log_action(
        db,
        current_user,
        "DEPARTMENT_STATUS_UPDATED",
        "department",
        dept.id,
        {"is_active": payload.is_active},
        request,
    )
    await db.commit()
    return DepartmentResponse.model_validate(dept)


@departments_router.delete("/{department_id}", status_code=204)
async def delete_department(
    request: Request,
    department_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Xóa mềm một bộ môn. Chặn xóa nếu vẫn còn giảng viên hoạt động liên kết.
    """
    await department_service.delete_department(db, department_id)
    await log_action(
        db,
        current_user,
        "DEPARTMENT_DELETED",
        "department",
        department_id,
        None,
        request,
    )
    await db.commit()


staffs_router = APIRouter()


# ──────────────────────────────────────────────
# Staff CRUD APIs
# ──────────────────────────────────────────────

@staffs_router.get("", response_model=StaffPaginationResponse)
async def list_staffs(
    page: int = Query(default=1, ge=1, description="Chỉ số trang (bắt đầu từ 1)"),
    page_size: int = Query(default=10, ge=1, le=1000, description="Số lượng giảng viên trên mỗi trang"),
    search: Optional[str] = Query(default=None, description="Tìm kiếm theo họ tên hoặc tên tiếng Anh"),
    department_id: Optional[uuid.UUID] = Query(default=None, description="Lọc theo ID bộ môn"),
    position_id: Optional[uuid.UUID] = Query(default=None, description="Lọc theo ID chức vụ chính"),
    academic_title: Optional[str] = Query(default=None, description="Lọc theo học hàm"),
    degree: Optional[str] = Query(default=None, description="Lọc theo học vị"),
    is_active: Optional[bool] = Query(default=None, description="Lọc theo trạng thái hoạt động"),
    sort_by: str = Query(default="sort_order", description="Trường sắp xếp (full_name, sort_order, created_at)"),
    order: str = Query(default="asc", description="Hướng sắp xếp (asc, desc)"),
    db: AsyncSession = Depends(get_db),
) -> StaffPaginationResponse:
    """
    Lấy danh sách giảng viên phân trang, hỗ trợ tìm kiếm, lọc nâng cao và sắp xếp động.
    """
    # Validation sort_by
    allowed_sort_fields = {"full_name", "sort_order", "created_at"}
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

    items, total = await staff_service.list_staffs(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        department_id=department_id,
        position_id=position_id,
        academic_title=academic_title,
        degree=degree,
        is_active=is_active,
        sort_by=sort_by,
        order=order,
    )

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return StaffPaginationResponse(
        items=[StaffResponse.model_validate(i) for i in items],
        page=page,
        page_size=page_size,
        total_items=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
    )



@staffs_router.get("/stats", response_model=StaffStatsResponse)
async def get_staffs_stats(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StaffStatsResponse:
    """
    Lấy số liệu thống kê tổng quan về đội ngũ giảng viên và trình độ.
    Yêu cầu quyền Admin/Manager (phải đăng nhập).
    """
    stats = await staff_service.get_stats(db)
    return StaffStatsResponse.model_validate(stats)


@staffs_router.get("/slug/{slug}", response_model=StaffResponse)
async def get_staff_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> StaffResponse:
    """
    Lấy chi tiết thông tin một giảng viên theo Slug (phục vụ SEO Portal).
    """
    staff = await staff_service.get_staff_by_slug(db, slug)
    return StaffResponse.model_validate(staff)


@staffs_router.get("/{staff_id}", response_model=StaffResponse)
async def get_staff(
    staff_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> StaffResponse:
    """
    Lấy chi tiết thông tin một giảng viên theo ID.
    """
    staff = await staff_service.get_staff_by_id(db, staff_id)
    return StaffResponse.model_validate(staff)


@staffs_router.post("", response_model=StaffResponse, status_code=201)
async def create_staff(
    request: Request,
    payload: StaffCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StaffResponse:
    """
    Tạo hồ sơ giảng viên mới. Tự động sinh slug độc nhất và kiểm tra khóa ngoại bộ môn/chức vụ.
    """
    staff = await staff_service.create_staff(db, payload)
    await log_action(
        db,
        current_user,
        "STAFF_CREATED",
        "staff",
        staff.id,
        {"full_name": staff.full_name},
        request,
    )
    await db.commit()
    return StaffResponse.model_validate(staff)


@staffs_router.put("/{staff_id}", response_model=StaffResponse)
async def update_staff(
    request: Request,
    staff_id: uuid.UUID,
    payload: StaffUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StaffResponse:
    """
    Cập nhật thông tin chi tiết một giảng viên. Cập nhật lại slug nếu đổi tên.
    """
    staff = await staff_service.update_staff(db, staff_id, payload)
    await log_action(
        db,
        current_user,
        "STAFF_UPDATED",
        "staff",
        staff.id,
        payload.model_dump(exclude_unset=True),
        request,
    )
    await db.commit()
    return StaffResponse.model_validate(staff)


@staffs_router.patch("/{staff_id}/status", response_model=StaffResponse)
async def update_staff_status(
    request: Request,
    staff_id: uuid.UUID,
    payload: StaffStatusUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StaffResponse:
    """
    Cập nhật nhanh trạng thái hoạt động (bật/tắt) của giảng viên.
    """
    staff = await staff_service.update_staff_status(db, staff_id, payload.is_active)
    await log_action(
        db,
        current_user,
        "STAFF_STATUS_UPDATED",
        "staff",
        staff.id,
        {"is_active": payload.is_active},
        request,
    )
    await db.commit()
    return StaffResponse.model_validate(staff)


@staffs_router.delete("/{staff_id}", status_code=204)
async def delete_staff(
    request: Request,
    staff_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Xóa mềm một hồ sơ giảng viên.
    """
    await staff_service.delete_staff(db, staff_id)
    await log_action(
        db,
        current_user,
        "STAFF_DELETED",
        "staff",
        staff_id,
        None,
        request,
    )
    await db.commit()


