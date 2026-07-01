from __future__ import annotations
import uuid
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, model_validator
from app.modules.menu.models import MenuItemTargetType
from app.modules.menu.schemas.common import build_menu_item_resolved


class PortalTargetInfo(BaseModel):
    """Thông tin target đã resolve chỉ chứa title và slug cho Portal Client."""
    title: str
    slug: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_title(cls, data: Any) -> Any:
        if not data:
            return data
        if isinstance(data, dict):
            title = data.get("title") or data.get("name")
            return {
                "title": title,
                "slug": data.get("slug")
            }
        title = getattr(data, "title", None) or getattr(data, "name", None)
        slug = getattr(data, "slug", None)
        return {
            "title": title,
            "slug": slug
        }


class PortalMenuItemResponse(BaseModel):
    """Response MenuItem phẳng làm phẳng sạch sẽ cho Portal Client."""
    id: uuid.UUID
    menu_id: uuid.UUID
    parent_id: Optional[uuid.UUID] = None
    target_type: Optional[MenuItemTargetType] = None
    target_id: Optional[uuid.UUID] = None
    target_info: Optional[PortalTargetInfo] = None
    external_url: Optional[str] = None
    open_in_new_tab: bool
    depth: int
    sort_order: int
    is_visible: bool
    has_link: bool = False
    title: str = ""

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_menu_item_before_validation(cls, data: Any) -> Any:
        return build_menu_item_resolved(data)


class PortalMenuItemTreeNode(BaseModel):
    """Node trong cây menu đệ quy làm phẳng cho Portal Client (Website)."""
    id: uuid.UUID
    menu_id: uuid.UUID
    parent_id: Optional[uuid.UUID] = None
    target_type: Optional[MenuItemTargetType] = None
    target_id: Optional[uuid.UUID] = None
    target_info: Optional[PortalTargetInfo] = None
    external_url: Optional[str] = None
    open_in_new_tab: bool
    depth: int
    sort_order: int
    is_visible: bool
    has_link: bool = False
    title: str = ""
    children: list["PortalMenuItemTreeNode"] = []

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_menu_item_before_validation(cls, data: Any) -> Any:
        return build_menu_item_resolved(data)


class PortalMenuTreeResponse(BaseModel):
    """Response cây menu phẳng gọn nhẹ cho Portal Client."""
    id: uuid.UUID
    name: str
    code: str
    description: Optional[str] = None
    is_active: bool
    items: list[PortalMenuItemTreeNode] = []

    model_config = ConfigDict(from_attributes=True)
