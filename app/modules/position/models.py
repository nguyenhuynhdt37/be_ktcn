import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.models.base import BaseModel
from app.modules.language.models import Language


class Position(BaseModel):
    """
    Model đại diện cho bảng chức vụ (positions).
    Quản lý các chức vụ công tác của giảng viên.
    """
    __tablename__ = "positions"

    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Soft Delete
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True, index=True
    )

    # Relationships
    translations: Mapped[List["PositionTranslation"]] = relationship(
        "PositionTranslation",
        back_populates="position",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    staffs: Mapped[List["Staff"]] = relationship(
        "Staff",
        back_populates="position",
        cascade="all, delete-orphan",
        passive_deletes=True
    )


class PositionTranslation(BaseModel):
    """
    Bảng dịch của Position.
    """
    __tablename__ = "position_translations"

    position_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("positions.id", ondelete="CASCADE"), nullable=False
    )
    language_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("languages.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    position: Mapped["Position"] = relationship("Position", back_populates="translations")
    language: Mapped["Language"] = relationship("Language", lazy="joined")

    __table_args__ = (
        UniqueConstraint("position_id", "language_id", name="uq_position_language_unique"),
    )
