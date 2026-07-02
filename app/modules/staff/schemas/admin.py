import uuid
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, model_validator
from app.modules.staff.schemas.common import build_staff_resolved
from app.modules.department.schemas import AdminDepartmentResponse
from app.modules.position.schemas import AdminPositionResponse


class AdminStaffResponse(BaseModel):
    """Response thông tin Giảng viên phục vụ quản trị."""
    id: uuid.UUID
    department_id: uuid.UUID
    position_id: uuid.UUID
    academic_title_id: Optional[uuid.UUID] = None
    degree_id: Optional[uuid.UUID] = None
    full_name: str
    english_name: Optional[str] = None
    slug: str
    avatar_object_key: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    office: Optional[str] = None
    sort_order: int
    is_active: bool
    is_translated: dict[str, bool] = {}
    translations: dict[str, Any] = {}
    academic_title: Optional[str] = None
    degree: Optional[str] = None
    biography: Optional[str] = None
    research_interests: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Eager relationships if loaded
    department: Optional[AdminDepartmentResponse] = None
    position: Optional[AdminPositionResponse] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_staff_before_validation(cls, data: Any) -> Any:
        return build_staff_resolved(data)


class StaffPaginationResponse(BaseModel):
    """Response phân trang danh sách giảng viên."""
    items: list[AdminStaffResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class TableStats(BaseModel):
    total: int
    active: int
    inactive: int


class FacultyStaffStatsResponse(BaseModel):
    departments: TableStats
    positions: TableStats
    staffs: TableStats
