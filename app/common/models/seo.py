import uuid
from typing import Optional

from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, declared_attr

from app.modules.media.models import MediaItem


class SEOMixin:
    """
    Mixin cung cấp đầy đủ các trường cấu hình SEO tùy chỉnh.
    Có thể kế thừa cho bất kỳ Model nào cần quản lý SEO (Category, Article, Page...).
    """
    seo_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    seo_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    seo_keywords: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    seo_canonical: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    seo_robots: Mapped[Optional[str]] = mapped_column(String(50), default="index, follow", nullable=True)
    
    seo_og_image_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("media_items.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    @declared_attr
    def seo_og_image(cls) -> Mapped[Optional[MediaItem]]:
        return relationship(MediaItem, foreign_keys=[cls.seo_og_image_id])
