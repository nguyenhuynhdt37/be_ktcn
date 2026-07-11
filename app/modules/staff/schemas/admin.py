import uuid
from datetime import date, datetime
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
    normalized_full_name: Optional[str] = None
    english_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    slug: str
    avatar_object_key: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    office: Optional[str] = None
    sort_order: int
    is_active: bool
    profile_status: str
    is_visible: bool
    note: Optional[str] = None
    source_type: Optional[str] = None
    source_note: Optional[str] = None
    source_file_id: Optional[uuid.UUID] = None
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
