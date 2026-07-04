import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime, Integer, String, Text, UniqueConstraint, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.models.base import BaseModel
from app.modules.language.models import Language


class Tag(BaseModel):
    """
    Model đại diện cho Tag dùng chung trong hệ thống CMS.
    Hỗ trợ gán nhãn cho nhiều thực thể (Article, Page, v.v.).
    """
    __tablename__ = "tags"

    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)  # Mã HEX, ví dụ: #FF5733
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    # Soft delete support
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True, index=True
    )

    articles: Mapped[list["Article"]] = relationship(
        "Article",
        secondary="article_tags",
        back_populates="tags"
    )

    translations: Mapped[list["TagTranslation"]] = relationship(
        "TagTranslation",
        back_populates="tag",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class TagTranslation(BaseModel):
    """
    Model lưu trữ các bản dịch đa ngôn ngữ chi tiết của Tag.
    """
    __tablename__ = "tag_translations"

    tag_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"), nullable=False, index=True
    )
    language_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("languages.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    # Các trường nội dung dịch
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    tag: Mapped["Tag"] = relationship("Tag", back_populates="translations")
    language: Mapped["Language"] = relationship("Language", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("tag_id", "language_id", name="uq_tag_language_unique"),
        UniqueConstraint("language_id", "slug", name="uq_tag_language_slug_unique"),
        Index("ix_tag_translations_tag_language", "tag_id", "language_id"),
        Index("ix_tag_translations_language_slug", "language_id", "slug"),
    )
