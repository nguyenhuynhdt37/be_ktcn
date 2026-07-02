import uuid
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, model_validator
from app.modules.department.schemas.common import build_department_resolved


class PortalDepartmentResponse(BaseModel):
    """Response thông tin Bộ môn làm phẳng (đã dịch) cho Portal Client."""
    id: uuid.UUID
    thumbnail_object_key: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    office: Optional[str] = None
    sort_order: int
    name: str = ""
    description: Optional[str] = None
    slug: str = ""
    staff_count: int = 0

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_department_before_validation(cls, data: Any) -> Any:
        return build_department_resolved(data)
