import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.models.base import BaseModel
from app.modules.language.models import Language


class AcademicTitle(BaseModel):
    """
    Model đại diện cho bảng học hàm (academic_titles).
    """
    __tablename__ = "academic_titles"

    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Soft Delete
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True, index=True
    )

    # Relationships
    translations: Mapped[List["AcademicTitleTranslation"]] = relationship(
        "AcademicTitleTranslation",
        back_populates="academic_title",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    staffs: Mapped[List["Staff"]] = relationship(
        "Staff",
        back_populates="academic_title"
    )


class AcademicTitleTranslation(BaseModel):
    """
    Bảng dịch của AcademicTitle.
    """
    __tablename__ = "academic_title_translations"

    academic_title_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("academic_titles.id", ondelete="CASCADE"), nullable=False
    )
    language_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("languages.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    abbreviation: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Relationships
    academic_title: Mapped["AcademicTitle"] = relationship("AcademicTitle", back_populates="translations")
    language: Mapped["Language"] = relationship("Language", lazy="joined")

    __table_args__ = (
        UniqueConstraint("academic_title_id", "language_id", name="uq_academic_title_language_unique"),
    )
