import uuid
from datetime import date, datetime
from typing import List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.models.base import BaseModel
from app.modules.language.models import Language
from app.modules.department.models import Department
from app.modules.position.models import Position
from app.modules.academic_title.models import AcademicTitle
from app.modules.degree.models import Degree


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
    academic_title_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("academic_titles.id", ondelete="SET NULL"), nullable=True
    )
    degree_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("degrees.id", ondelete="SET NULL"), nullable=True
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    english_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_object_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    office: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    profile_status: Mapped[str] = mapped_column(String(30), default="imported", nullable=False)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    source_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_file_id: Mapped[Optional[uuid.UUID]] = mapped_column(nullable=True)
    
    # Soft Delete
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True, index=True
    )

    # Relationships
    department: Mapped["Department"] = relationship("Department", back_populates="staffs")
    position: Mapped["Position"] = relationship("Position", back_populates="staffs")
    academic_title: Mapped[Optional["AcademicTitle"]] = relationship("AcademicTitle", back_populates="staffs")
    degree: Mapped[Optional["Degree"]] = relationship("Degree", back_populates="staffs")
    
    translations: Mapped[List["StaffTranslation"]] = relationship(
        "StaffTranslation",
        back_populates="staff",
        cascade="all, delete-orphan",
        lazy="selectin"
    )


class StaffTranslation(BaseModel):
    """
    Bảng dịch của Staff.
    """
    __tablename__ = "staff_translations"

    staff_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("staffs.id", ondelete="CASCADE"), nullable=False
    )
    language_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("languages.id", ondelete="RESTRICT"), nullable=False
    )
    biography: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    research_interests: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    staff: Mapped["Staff"] = relationship("Staff", back_populates="translations")
    language: Mapped["Language"] = relationship("Language", lazy="joined")

    __table_args__ = (
        UniqueConstraint("staff_id", "language_id", name="uq_staff_language_unique"),
    )
