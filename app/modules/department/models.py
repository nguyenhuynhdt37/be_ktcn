import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.models.base import BaseModel
from app.modules.language.models import Language


class Department(BaseModel):
    """
    Model đại diện cho bảng bộ môn (departments).
    Quản lý thông tin bộ môn/khoa của trường.
    """
    __tablename__ = "departments"

    thumbnail_object_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    office: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Soft Delete
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True, index=True
    )

    # Relationships
    translations: Mapped[List["DepartmentTranslation"]] = relationship(
        "DepartmentTranslation",
        back_populates="department",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    staffs: Mapped[List["Staff"]] = relationship(
        "Staff",
        back_populates="department",
        cascade="all, delete-orphan",
        passive_deletes=True
    )


class DepartmentTranslation(BaseModel):
    """
    Bảng dịch của Department.
    """
    __tablename__ = "department_translations"

    department_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("departments.id", ondelete="CASCADE"), nullable=False
    )
    language_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("languages.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationships
    department: Mapped["Department"] = relationship("Department", back_populates="translations")
    language: Mapped["Language"] = relationship("Language", lazy="joined")

    __table_args__ = (
        UniqueConstraint("department_id", "language_id", name="uq_department_language_unique"),
    )
