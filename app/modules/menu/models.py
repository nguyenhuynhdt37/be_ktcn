import enum
import uuid
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.models.base import BaseModel


class MenuItemTargetType(str, enum.Enum):
    """Loại tài nguyên mà Menu Item có thể liên kết tới."""

    CATEGORY = "CATEGORY"
    ARTICLE = "ARTICLE"
    PAGE = "PAGE"
    DEPARTMENT = "DEPARTMENT"
    MODULE = "MODULE"
    EXTERNAL_LINK = "EXTERNAL_LINK"



class Menu(BaseModel):
    """
    Đại diện cho một khu vực menu (Header, Sidebar, Footer...).
    Mỗi Menu có một code duy nhất để frontend query.
    """

    __tablename__ = "menus"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    items: Mapped[List["MenuItem"]] = relationship(
        "MenuItem",
        back_populates="menu",
        cascade="all, delete-orphan",
        order_by="MenuItem.sort_order",
    )


class MenuItem(BaseModel):
    """
    Một mục trong menu, hỗ trợ lồng tối đa 3 cấp thông qua parent_id.
    Có thể liên kết tới nhiều loại tài nguyên khác nhau (Polymorphic Association).
    """

    __tablename__ = "menu_items"
    __table_args__ = (
        CheckConstraint(
            "depth >= 1 AND depth <= 3",
            name="chk_menu_items_depth",
        ),
        CheckConstraint(
            """
            (target_type = 'EXTERNAL_LINK' AND external_url IS NOT NULL AND target_id IS NULL)
            OR (target_type IS NOT NULL AND target_type != 'EXTERNAL_LINK' AND target_id IS NOT NULL AND external_url IS NULL)
            OR (target_type IS NULL AND target_id IS NULL AND external_url IS NULL)
            """,
            name="chk_menu_items_target_consistency",
        ),
    )

    menu_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("menus.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("menu_items.id", ondelete="CASCADE"), nullable=True, index=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)

    # Polymorphic target
    target_type: Mapped[Optional[MenuItemTargetType]] = mapped_column(
        Enum(MenuItemTargetType, name="menu_item_target_type", native_enum=False),
        nullable=True,
    )
    target_id: Mapped[Optional[uuid.UUID]] = mapped_column(nullable=True)
    external_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    open_in_new_tab: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # Display
    icon: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    depth: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    menu: Mapped["Menu"] = relationship("Menu", back_populates="items")
    parent: Mapped[Optional["MenuItem"]] = relationship(
        "MenuItem", remote_side="MenuItem.id", back_populates="children"
    )
    children: Mapped[List["MenuItem"]] = relationship(
        "MenuItem",
        back_populates="parent",
        cascade="all, delete-orphan",
        order_by="MenuItem.sort_order",
    )
