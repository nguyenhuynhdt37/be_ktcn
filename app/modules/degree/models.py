import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.models.base import BaseModel
from app.modules.language.models import Language


class Degree(BaseModel):
    """
    Model đại diện cho bảng học vị (degrees).
    """
    __tablename__ = "degrees"

    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Soft Delete
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True, index=True
    )

    # Relationships
    translations: Mapped[List["DegreeTranslation"]] = relationship(
        "DegreeTranslation",
        back_populates="degree",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    staffs: Mapped[List["Staff"]] = relationship(
        "Staff",
        back_populates="degree"
    )


class DegreeTranslation(BaseModel):
    """
    Bảng dịch của Degree.
    """
    __tablename__ = "degree_translations"

    degree_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("degrees.id", ondelete="CASCADE"), nullable=False
    )
    language_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("languages.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    abbreviation: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Relationships
    degree: Mapped["Degree"] = relationship("Degree", back_populates="translations")
    language: Mapped["Language"] = relationship("Language", lazy="joined")

    __table_args__ = (
        UniqueConstraint("degree_id", "language_id", name="uq_degree_language_unique"),
    )
