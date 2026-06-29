import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.models.base import BaseModel


class Department(BaseModel):
    """
    Model đại diện cho bảng bộ môn (departments).
    Quản lý thông tin bộ môn/khoa của trường.
    """
    __tablename__ = "departments"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    english_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
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
    staffs: Mapped[List["Staff"]] = relationship(
        "Staff", back_populates="department", cascade="all, delete-orphan", passive_deletes=True
    )

    __table_args__ = (
        Index(
            "uidx_departments_slug",
            "slug",
            unique=True,
            postgresql_where="deleted_at IS NULL"
        ),
        Index(
            "idx_departments_list",
            "is_active",
            "sort_order",
            postgresql_where="deleted_at IS NULL"
        ),
    )


class Position(BaseModel):
    """
    Model đại diện cho bảng chức vụ (positions).
    Quản lý các chức vụ công tác của giảng viên.
    """
    __tablename__ = "positions"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    english_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Soft Delete
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True, index=True
    )

    # Relationships
    staffs: Mapped[List["Staff"]] = relationship(
        "Staff", back_populates="position", cascade="all, delete-orphan", passive_deletes=True
    )

    __table_args__ = (
        Index(
            "uidx_positions_name",
            "name",
            unique=True,
            postgresql_where="deleted_at IS NULL"
        ),
        Index(
            "idx_positions_list",
            "is_active",
            "sort_order",
            postgresql_where="deleted_at IS NULL"
        ),
    )


class Staff(BaseModel):
    """
    Model đại diện cho bảng giảng viên (staffs).
    Lưu hồ sơ thông tin giảng viên/cán bộ.
    """
    __tablename__ = "staffs"

    department_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False
    )
    position_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("positions.id", ondelete="RESTRICT"), nullable=False
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    english_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    academic_title: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    degree: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    avatar_object_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    office: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    biography: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    research_interests: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Soft Delete
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True, index=True
    )

    # Relationships
    department: Mapped[Department] = relationship("Department", back_populates="staffs")
    position: Mapped[Position] = relationship("Position", back_populates="staffs")

    __table_args__ = (
        Index(
            "uidx_staff_slug",
            "slug",
            unique=True,
            postgresql_where="deleted_at IS NULL"
        ),
        Index(
            "idx_staff_department",
            "department_id",
            "is_active",
            "sort_order",
            postgresql_where="deleted_at IS NULL"
        ),
        Index(
            "idx_staff_position",
            "position_id",
            "is_active",
            "sort_order",
            postgresql_where="deleted_at IS NULL"
        ),
        Index(
            "idx_staff_name",
            "full_name"
        ),
        Index(
            "idx_staff_active",
            "is_active",
            postgresql_where="deleted_at IS NULL"
        ),
    )
