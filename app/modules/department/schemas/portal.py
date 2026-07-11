import uuid
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, model_validator
from app.modules.department.schemas.common import build_department_resolved


class PortalDepartmentResponse(BaseModel):
    """Response thông tin Bộ môn làm phẳng (đã dịch) cho Portal Client."""
    id: uuid.UUID
    thumbnail_object_key: Optional[str] = None
    logo_object_key: Optional[str] = None
    banner_object_key: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    office: Optional[str] = None
    sort_order: int
    display_order: Optional[int] = None
    head_staff_id: Optional[uuid.UUID] = None
    name: str = ""
    description: Optional[str] = None
    slug: str = ""
    mission: Optional[str] = None
    vision: Optional[str] = None
    history: Optional[str] = None
    research_overview: Optional[str] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    staff_count: int = 0

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_department_before_validation(cls, data: Any) -> Any:
        return build_department_resolved(data)
