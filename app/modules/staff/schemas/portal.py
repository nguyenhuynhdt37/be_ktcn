import uuid
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, model_validator
from app.modules.staff.schemas.common import build_staff_resolved
from app.modules.department.schemas import PortalDepartmentResponse
from app.modules.position.schemas import PortalPositionResponse


class PortalStaffResponse(BaseModel):
    """Response thông tin Giảng viên phẳng (đã dịch) cho Portal Website."""
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
    profile_status: str
    academic_title: Optional[str] = None
    degree: Optional[str] = None
    biography: Optional[str] = None
    research_interests: Optional[str] = None

    department: Optional[PortalDepartmentResponse] = None
    position: Optional[PortalPositionResponse] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_staff_before_validation(cls, data: Any) -> Any:
        return build_staff_resolved(data)
