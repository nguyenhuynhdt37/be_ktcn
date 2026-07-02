import uuid
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, model_validator
from app.modules.department.schemas.common import build_department_resolved


class AdminDepartmentResponse(BaseModel):
    """Response thông tin Bộ môn phục vụ quản trị."""
    id: uuid.UUID
    thumbnail_object_key: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    office: Optional[str] = None
    sort_order: int
    is_active: bool
    is_translated: dict[str, bool] = {}
    translations: dict[str, Any] = {}
    name: str = ""
    description: Optional[str] = None
    slug: str = ""
    staff_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_department_before_validation(cls, data: Any) -> Any:
        return build_department_resolved(data)


class DepartmentPaginationResponse(BaseModel):
    """Response phân trang danh sách bộ môn."""
    items: list[AdminDepartmentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class DepartmentStatsResponse(BaseModel):
    total: int
    active: int
    inactive: int
