import uuid
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, model_validator
from app.modules.position.schemas.common import build_position_resolved


class AdminPositionResponse(BaseModel):
    """Response thông tin Chức vụ phục vụ quản trị (Admin CMS)."""
    id: uuid.UUID
    sort_order: int
    is_active: bool
    is_translated: dict[str, bool] = {}
    translations: dict[str, Any] = {}
    name: str = ""
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_position_before_validation(cls, data: Any) -> Any:
        return build_position_resolved(data)


class PositionPaginationResponse(BaseModel):
    """Response phân trang danh sách chức vụ."""
    items: list[AdminPositionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class PositionStatsResponse(BaseModel):
    total: int
    active: int
    inactive: int
