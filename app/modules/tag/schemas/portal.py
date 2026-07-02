from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, model_validator
from app.modules.tag.schemas.common import build_tag_resolved_before_validation


class PortalTagResponse(BaseModel):
    id: uuid.UUID
    color: Optional[str] = None
    usage_count: int
    article_count: int = 0
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    name: str = ""
    slug: str = ""
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_tag_before_validation(cls, data: Any) -> Any:
        return build_tag_resolved_before_validation(data)
