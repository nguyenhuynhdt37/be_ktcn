import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.models.base import BaseModel

if TYPE_CHECKING:
    from app.modules.department.models import Department
    from app.modules.language.models import Language
    from app.modules.media.models import MediaItem


class DepartmentGallery(BaseModel):
    __tablename__ = "department_galleries"

    department_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("departments.id", ondelete="CASCADE"), index=True)
    cover_object_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    department: Mapped["Department"] = relationship("Department", back_populates="galleries")
    translations: Mapped[list["DepartmentGalleryTranslation"]] = relationship(
        "DepartmentGalleryTranslation", back_populates="gallery", cascade="all, delete-orphan", lazy="selectin"
    )
    items: Mapped[list["DepartmentGalleryItem"]] = relationship(
        "DepartmentGalleryItem", back_populates="gallery", cascade="all, delete-orphan", lazy="selectin",
        order_by="DepartmentGalleryItem.sort_order"
    )


class DepartmentGalleryTranslation(BaseModel):
    __tablename__ = "department_gallery_translations"

    gallery_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("department_galleries.id", ondelete="CASCADE"), index=True)
    language_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("languages.id", ondelete="RESTRICT"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    gallery: Mapped["DepartmentGallery"] = relationship("DepartmentGallery", back_populates="translations")
    language: Mapped["Language"] = relationship("Language", lazy="joined")

    __table_args__ = (UniqueConstraint("gallery_id", "language_id", name="uq_department_gallery_language"),)


class DepartmentGalleryItem(BaseModel):
    __tablename__ = "department_gallery_items"

    gallery_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("department_galleries.id", ondelete="CASCADE"), index=True)
    media_item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("media_items.id", ondelete="RESTRICT"), index=True)
    caption: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    alt_text: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    gallery: Mapped["DepartmentGallery"] = relationship("DepartmentGallery", back_populates="items")
    media_item: Mapped["MediaItem"] = relationship("MediaItem", lazy="joined")
