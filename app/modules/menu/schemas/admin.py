from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.modules.menu.models import MenuItemTargetType
from app.modules.menu.target_resolver import TargetInfo
from app.modules.menu.schemas.common import build_menu_item_resolved


class AdminMenuResponse(BaseModel):
    """Response cho thông tin Menu phục vụ quản trị."""
    id: uuid.UUID
    name: str
    code: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminMenuItemResponse(BaseModel):
    """Response cho thông tin Menu Item phẳng phục vụ quản trị."""
    id: uuid.UUID
    menu_id: uuid.UUID
    parent_id: Optional[uuid.UUID] = None
    target_type: Optional[MenuItemTargetType] = None
    target_id: Optional[uuid.UUID] = None
    target_info: Optional[TargetInfo] = None
    external_url: Optional[str] = None
    open_in_new_tab: bool
    depth: int
    sort_order: int
    is_visible: bool
    has_link: bool = False
    is_translated: dict[str, bool] = {}
    translations: dict[str, Any] = {}
    title: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_menu_item_before_validation(cls, data: Any) -> Any:
        return build_menu_item_resolved(data)


class AdminMenuItemTreeNode(BaseModel):
    """Response node trong cây menu đệ quy phục vụ quản trị (Admin CMS)."""
    id: uuid.UUID
    menu_id: uuid.UUID
    parent_id: Optional[uuid.UUID] = None
    target_type: Optional[MenuItemTargetType] = None
    target_id: Optional[uuid.UUID] = None
    target_info: Optional[TargetInfo] = None
    external_url: Optional[str] = None
    open_in_new_tab: bool
    depth: int
    sort_order: int
    is_visible: bool
    has_link: bool = False
    is_translated: dict[str, bool] = {}
    translations: dict[str, Any] = {}
    title: str = ""
    children: list["AdminMenuItemTreeNode"] = []

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_menu_item_before_validation(cls, data: Any) -> Any:
        return build_menu_item_resolved(data)


class AdminMenuTreeResponse(BaseModel):
    """Response cây menu đầy đủ phục vụ quản trị."""
    id: uuid.UUID
    name: str
    code: str
    description: Optional[str] = None
    is_active: bool
    items: list[AdminMenuItemTreeNode] = []

    model_config = ConfigDict(from_attributes=True)
