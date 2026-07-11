import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.models.base import BaseModel

if TYPE_CHECKING:
    from app.modules.article.models import Article
    from app.modules.department.models import Department
    from app.modules.language.models import Language


class Program(BaseModel):
    __tablename__ = "programs"

    department_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("departments.id", ondelete="CASCADE"), index=True)
    code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, unique=True)
    degree_level: Mapped[str] = mapped_column(String(50), default="bachelor")
    duration_years: Mapped[Optional[float]] = mapped_column(Numeric(3, 1), nullable=True)
    training_mode: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    thumbnail_object_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    department: Mapped["Department"] = relationship("Department", back_populates="programs")
    translations: Mapped[list["ProgramTranslation"]] = relationship(
        "ProgramTranslation", back_populates="program", cascade="all, delete-orphan", lazy="selectin"
    )
    articles: Mapped[list["Article"]] = relationship("Article", back_populates="program")


class ProgramTranslation(BaseModel):
    __tablename__ = "program_translations"

    program_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("programs.id", ondelete="CASCADE"), index=True)
    language_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("languages.id", ondelete="RESTRICT"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255))
    short_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    career_opportunities: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    admissions_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    program: Mapped["Program"] = relationship("Program", back_populates="translations")
    language: Mapped["Language"] = relationship("Language", lazy="joined")

    __table_args__ = (
        UniqueConstraint("program_id", "language_id", name="uq_program_language"),
        UniqueConstraint("language_id", "slug", name="uq_program_language_slug"),
    )
