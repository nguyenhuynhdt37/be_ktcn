from __future__ import annotations
import uuid
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, model_validator

from app.modules.category.schemas.common import build_seo_resolved_before_validation


class AdminCategoryResponse(BaseModel):
    """Response thông tin chi tiết đầy đủ của danh mục bài viết phục vụ quản trị."""
    id: uuid.UUID
    parent_id: Optional[uuid.UUID] = None
    thumbnail_id: Optional[uuid.UUID] = None
    status: str
    sort_order: int
    is_visible: bool
    is_weekly_schedule: bool
    is_locked: bool
    article_count: int = 0
    is_translated: dict[str, bool] = {}
    translations: dict[str, Any] = {}
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


class AdminCategoryTreeNode(BaseModel):
    """Node trong cây danh mục đầy đủ phục vụ render phía quản trị (Admin CMS)."""
    id: uuid.UUID
    parent_id: Optional[uuid.UUID] = None
    thumbnail_id: Optional[uuid.UUID] = None
    status: str
    sort_order: int
    is_visible: bool
    is_weekly_schedule: bool
    is_locked: bool
    article_count: int = 0
    is_translated: dict[str, bool] = {}
    translations: dict[str, Any] = {}
    name: str = ""
    slug: str = ""
    description: Optional[str] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    children: list["AdminCategoryTreeNode"] = []

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_seo_before_validation(cls, data: Any) -> Any:
        return build_seo_resolved_before_validation(data)
