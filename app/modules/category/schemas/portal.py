from __future__ import annotations
import uuid
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, model_validator

from app.modules.category.schemas.common import build_seo_resolved_before_validation


class PortalCategoryResponse(BaseModel):
    """Response thông tin phẳng tinh gọn cho Portal Client (không chứa các trường quản trị nội bộ)."""
    id: uuid.UUID
    parent_id: Optional[uuid.UUID] = None
    thumbnail_id: Optional[uuid.UUID] = None
    sort_order: int
    is_weekly_schedule: bool
    article_count: int = 0
    name: str = ""
    slug: str = ""
    description: Optional[str] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_seo_before_validation(cls, data: Any) -> Any:
        return build_seo_resolved_before_validation(data)


class PortalCategoryTreeNode(BaseModel):
    """Node trong cây danh mục phẳng gọn nhẹ cho Portal Client (không translations/status/locked)."""
    id: uuid.UUID
    parent_id: Optional[uuid.UUID] = None
    thumbnail_id: Optional[uuid.UUID] = None
    sort_order: int
    is_weekly_schedule: bool
    article_count: int = 0
    name: str = ""
    slug: str = ""
    description: Optional[str] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    children: list["PortalCategoryTreeNode"] = []

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_seo_before_validation(cls, data: Any) -> Any:
        return build_seo_resolved_before_validation(data)
