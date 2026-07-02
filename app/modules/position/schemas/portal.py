import uuid
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, model_validator
from app.modules.position.schemas.common import build_position_resolved


class PortalPositionResponse(BaseModel):
    """Response thông tin Chức vụ phẳng (đã dịch) cho Portal Website."""
    id: uuid.UUID
    sort_order: int
    name: str = ""
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_position_before_validation(cls, data: Any) -> Any:
        return build_position_resolved(data)
