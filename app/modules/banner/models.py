import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text, Enum, text
from sqlalchemy.orm import Mapped, mapped_column

from app.common.models.base import BaseModel

class BannerPosition(str, enum.Enum):
    HOME_HERO = "HOME_HERO"
    HOME_POPUP = "HOME_POPUP"
    HOME_TOP = "HOME_TOP"
    NEWS_TOP = "NEWS_TOP"
    CATEGORY_TOP = "CATEGORY_TOP"
    PAGE_TOP = "PAGE_TOP"


class Banner(BaseModel):
    """
    Model quản lý thông tin Banner hiển thị trên trang Portal học sinh.
    """
    __tablename__ = "banners"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    desktop_image_object_key: Mapped[str] = mapped_column(String(512), nullable=False)
    mobile_image_object_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    link_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    open_in_new_tab: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    position: Mapped[BannerPosition] = mapped_column(
        Enum(BannerPosition, name="banner_position"), nullable=False
    )

    sort_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    start_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Soft Delete
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )

    __table_args__ = (
        Index("idx_banner_position", "position"),
        Index(
            "idx_banner_active",
            "is_active",
            postgresql_where=text("deleted_at IS NULL")
        ),
        Index(
            "idx_banner_sort",
            "position",
            "sort_order",
            postgresql_where=text("deleted_at IS NULL")
        ),
        Index("idx_banner_start", "start_at"),
        Index("idx_banner_end", "end_at"),
    )
