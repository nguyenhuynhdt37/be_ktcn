from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator
from app.modules.tag.schemas.common import build_tag_resolved_before_validation


class TranslationItemResponse(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TagCreate(BaseModel):
    color: Optional[str] = Field(
        default=None,
        max_length=7,
        pattern=r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$",
        description="Mã màu HEX đại diện cho Tag, ví dụ: #FF5733"
    )
    sort_order: int = Field(default=0, description="Thứ tự sắp xếp")
    is_active: bool = Field(default=True, description="Trạng thái hoạt động")
    translations: dict[str, TranslationItemResponse] = Field(..., description="Bản dịch của Tag")


class TagUpdate(BaseModel):
    color: Optional[str] = Field(
        default=None,
        max_length=7,
        pattern=r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$"
    )
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    translations: Optional[dict[str, TranslationItemResponse]] = None


class AdminTagResponse(BaseModel):
    id: uuid.UUID
    color: Optional[str] = None
    usage_count: int
    article_count: int = 0
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    is_translated: dict[str, bool] = {}
    translations: dict[str, Any] = {}
    name: str = ""
    slug: str = ""
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_tag_before_validation(cls, data: Any) -> Any:
        return build_tag_resolved_before_validation(data)
