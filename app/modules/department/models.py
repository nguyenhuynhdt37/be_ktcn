import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.models.base import BaseModel
from app.modules.language.models import Language


class Department(BaseModel):
    """
    Model đại diện cho bảng bộ môn (departments).
    Quản lý thông tin bộ môn/khoa của trường.
    """
    __tablename__ = "departments"
    __table_args__ = (
        Index(
            "uidx_department_code",
            "code",
            unique=True,
            postgresql_where=text("deleted_at IS NULL AND code IS NOT NULL"),
        ),
        Index("idx_department_unit_type", "unit_type"),
        Index("idx_department_parent_id", "parent_id"),
    )

    code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    unit_type: Mapped[str] = mapped_column(String(30), default="department", nullable=False)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    thumbnail_object_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    logo_object_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    banner_object_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    office: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    display_order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Trưởng Khoa / Head of Department
    head_staff_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("staffs.id", ondelete="SET NULL"), nullable=True
    )

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
        passive_deletes=True,
        foreign_keys="[Staff.department_id]"
    )

    head_staff: Mapped[Optional["Staff"]] = relationship(
        "Staff",
        foreign_keys=[head_staff_id],
        lazy="selectin"
    )

    parent: Mapped[Optional["Department"]] = relationship(
        "Department", remote_side="Department.id", back_populates="children"
    )
    children: Mapped[List["Department"]] = relationship(
        "Department", back_populates="parent"
    )
    programs: Mapped[List["Program"]] = relationship(
        "Program", back_populates="department", cascade="all, delete-orphan"
    )
    galleries: Mapped[List["DepartmentGallery"]] = relationship(
        "DepartmentGallery", back_populates="department", cascade="all, delete-orphan"
    )
    articles: Mapped[List["Article"]] = relationship("Article", back_populates="department")


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
    mission: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    vision: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    history: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    research_overview: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    seo_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    seo_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationships
    department: Mapped["Department"] = relationship("Department", back_populates="translations")
    language: Mapped["Language"] = relationship("Language", lazy="joined")

    __table_args__ = (
        UniqueConstraint("department_id", "language_id", name="uq_department_language_unique"),
    )
