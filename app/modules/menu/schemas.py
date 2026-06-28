import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.menu.models import MenuItemTargetType
from app.modules.menu.target_resolver import TargetInfo


# ──────────────────────────────────────────────
# Icon Picker Schemas
# ──────────────────────────────────────────────

class IconItem(BaseModel):
    name: str = Field(..., description="Tên hiển thị thân thiện (Ví dụ: Thư viện)")
    code: str = Field(..., description="Mã class CSS hoặc tên Lucide icon (Ví dụ: library / BookOpen)")

class IconCategory(BaseModel):
    category: str = Field(..., description="Tên nhóm icon (Ví dụ: Học thuật, Tổ chức...)")
    icons: List[IconItem]


# ──────────────────────────────────────────────
# Menu Schemas
# ──────────────────────────────────────────────


class MenuCreate(BaseModel):
    """Request body tạo Menu mới."""

    name: str = Field(..., max_length=100, description="Tên menu")
    code: str = Field(
        ..., max_length=50, pattern=r"^[a-z][a-z0-9_-]*$", description="Mã menu (lowercase, unique)"
    )
    description: Optional[str] = Field(default=None, description="Mô tả")
    is_active: bool = Field(default=True, description="Trạng thái hoạt động")


class MenuUpdate(BaseModel):
    """Request body cập nhật Menu."""

    name: Optional[str] = Field(default=None, max_length=100)
    code: Optional[str] = Field(default=None, max_length=50, pattern=r"^[a-z][a-z0-9_-]*$")
    description: Optional[str] = None
    is_active: Optional[bool] = None


class MenuResponse(BaseModel):
    """Response cho thông tin Menu."""

    id: uuid.UUID
    name: str
    code: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ──────────────────────────────────────────────
# Menu Item Schemas
# ──────────────────────────────────────────────


class MenuItemCreate(BaseModel):
    """Request body tạo Menu Item."""

    parent_id: Optional[uuid.UUID] = Field(default=None, description="ID item cha (NULL = root)")
    title: str = Field(..., max_length=255, description="Tiêu đề hiển thị")
    target_type: Optional[MenuItemTargetType] = Field(
        default=None, description="Loại tài nguyên liên kết"
    )
    target_id: Optional[uuid.UUID] = Field(
        default=None, description="ID tài nguyên liên kết"
    )
    external_url: Optional[str] = Field(
        default=None, max_length=500, description="URL ngoài (chỉ khi EXTERNAL_LINK)"
    )
    open_in_new_tab: bool = Field(default=False, description="Mở tab mới")
    icon: Optional[str] = Field(default=None, max_length=100, description="Icon class")
    sort_order: int = Field(default=0, ge=0, description="Thứ tự sắp xếp")
    is_visible: bool = Field(default=True, description="Hiển thị")

    @model_validator(mode="after")
    def validate_target_consistency(self) -> "MenuItemCreate":
        """Validate tính nhất quán giữa target_type, target_id và external_url."""
        if self.target_type == MenuItemTargetType.EXTERNAL_LINK:
            if not self.external_url:
                raise ValueError("external_url bắt buộc khi target_type = EXTERNAL_LINK")
            if self.target_id is not None:
                raise ValueError("target_id phải rỗng khi target_type = EXTERNAL_LINK")
        elif self.target_type is not None:
            if self.target_id is None:
                raise ValueError("target_id bắt buộc khi target_type không phải EXTERNAL_LINK")
            if self.external_url is not None:
                raise ValueError("external_url phải rỗng khi target_type không phải EXTERNAL_LINK")
        else:
            # target_type is None → label nhóm
            if self.target_id is not None or self.external_url is not None:
                raise ValueError(
                    "target_id và external_url phải rỗng khi target_type = NULL (label nhóm)"
                )
        return self


class MenuItemUpdate(BaseModel):
    """Request body cập nhật Menu Item (chi tiết config trong panel)."""

    title: Optional[str] = Field(default=None, max_length=255)
    target_type: Optional[MenuItemTargetType] = None
    target_id: Optional[uuid.UUID] = None
    external_url: Optional[str] = Field(default=None, max_length=500)
    open_in_new_tab: Optional[bool] = None
    icon: Optional[str] = Field(default=None, max_length=100)
    is_visible: Optional[bool] = None


class MenuItemResponse(BaseModel):
    """Response cho thông tin Menu Item (flat)."""

    id: uuid.UUID
    menu_id: uuid.UUID
    parent_id: Optional[uuid.UUID] = None
    title: str
    target_type: Optional[MenuItemTargetType] = None
    target_id: Optional[uuid.UUID] = None
    target_info: Optional[TargetInfo] = None
    external_url: Optional[str] = None
    open_in_new_tab: bool
    icon: Optional[str] = None
    depth: int
    sort_order: int
    is_visible: bool
    has_link: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ──────────────────────────────────────────────
# Tree Schemas
# ──────────────────────────────────────────────


class MenuItemTreeNode(BaseModel):
    """Response node trong cây menu (recursive)."""

    id: uuid.UUID
    title: str
    target_type: Optional[MenuItemTargetType] = None
    target_id: Optional[uuid.UUID] = None
    target_info: Optional[TargetInfo] = None
    external_url: Optional[str] = None
    open_in_new_tab: bool
    icon: Optional[str] = None
    depth: int
    sort_order: int
    is_visible: bool
    has_link: bool
    children: list["MenuItemTreeNode"] = []

    model_config = ConfigDict(from_attributes=True)


class MenuTreeResponse(BaseModel):
    """Response cây menu đầy đủ."""

    id: uuid.UUID
    name: str
    code: str
    description: Optional[str] = None
    is_active: bool
    items: list[MenuItemTreeNode] = []

    model_config = ConfigDict(from_attributes=True)


# ──────────────────────────────────────────────
# Reorder Schemas (Kéo thả)
# ──────────────────────────────────────────────


class ReorderItem(BaseModel):
    """Một item trong danh sách reorder — frontend gửi sau khi kéo thả."""

    id: uuid.UUID
    parent_id: Optional[uuid.UUID] = None
    sort_order: int = Field(ge=0)


class MenuItemReorderRequest(BaseModel):
    """
    Request body cho batch reorder (kéo thả).
    Frontend gửi toàn bộ items với parent_id + sort_order mới.
    """

    items: list[ReorderItem] = Field(
        ..., min_length=1, description="Danh sách items với vị trí mới"
    )
