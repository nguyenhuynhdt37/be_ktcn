import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.models.base import BaseModel

if TYPE_CHECKING:
    from app.modules.article.models import Article
    from app.modules.department.models import Department
    from app.modules.language.models import Language


class Program(BaseModel):
    __tablename__ = "programs"

    department_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("departments.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str | None] = mapped_column(String(50), nullable=True, unique=True)
    degree_level: Mapped[str] = mapped_column(String(50), default="bachelor")
    duration_years: Mapped[float | None] = mapped_column(Numeric(3, 1), nullable=True)
    training_mode: Mapped[str | None] = mapped_column(String(100), nullable=True)
    thumbnail_object_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    department: Mapped["Department"] = relationship(
        "Department", back_populates="programs"
    )
    translations: Mapped[list["ProgramTranslation"]] = relationship(
        "ProgramTranslation",
        back_populates="program",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    versions: Mapped[list["ProgramVersion"]] = relationship(
        "ProgramVersion",
        back_populates="program",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ProgramVersion.sort_order, ProgramVersion.version_year.desc()",
    )
    articles: Mapped[list["Article"]] = relationship(
        "Article", back_populates="program"
    )


class ProgramTranslation(BaseModel):
    __tablename__ = "program_translations"

    program_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("programs.id", ondelete="CASCADE"), index=True
    )
    language_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("languages.id", ondelete="RESTRICT"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255))
    short_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    career_opportunities: Mapped[str | None] = mapped_column(Text, nullable=True)
    admissions_info: Mapped[str | None] = mapped_column(Text, nullable=True)

    program: Mapped["Program"] = relationship("Program", back_populates="translations")
    language: Mapped["Language"] = relationship("Language", lazy="joined")

    __table_args__ = (
        UniqueConstraint("program_id", "language_id", name="uq_program_language"),
        UniqueConstraint("language_id", "slug", name="uq_program_language_slug"),
    )


class ProgramVersion(BaseModel):
    __tablename__ = "program_versions"

    program_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("programs.id", ondelete="CASCADE"), index=True
    )
    version_year: Mapped[int] = mapped_column(Integer)
    cohort_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    total_credits: Mapped[float | None] = mapped_column(Numeric(6, 1), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    program: Mapped["Program"] = relationship("Program", back_populates="versions")
    translations: Mapped[list["ProgramVersionTranslation"]] = relationship(
        "ProgramVersionTranslation",
        back_populates="version",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    documents: Mapped[list["ProgramDocument"]] = relationship(
        "ProgramDocument",
        back_populates="version",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ProgramDocument.sort_order, ProgramDocument.created_at",
    )
    outcomes: Mapped[list["ProgramOutcome"]] = relationship(
        "ProgramOutcome",
        back_populates="version",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ProgramOutcome.sort_order, ProgramOutcome.code",
    )
    courses: Mapped[list["ProgramCourse"]] = relationship(
        "ProgramCourse",
        back_populates="version",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ProgramCourse.sort_order, ProgramCourse.course_code",
    )

    __table_args__ = (
        UniqueConstraint("program_id", "version_year", name="uq_program_version_year"),
    )


class ProgramVersionTranslation(BaseModel):
    __tablename__ = "program_version_translations"

    version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("program_versions.id", ondelete="CASCADE"), index=True
    )
    language_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("languages.id", ondelete="RESTRICT"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    general_objective: Mapped[str | None] = mapped_column(Text, nullable=True)
    career_opportunities: Mapped[str | None] = mapped_column(Text, nullable=True)

    version: Mapped["ProgramVersion"] = relationship(
        "ProgramVersion", back_populates="translations"
    )
    language: Mapped["Language"] = relationship("Language", lazy="joined")

    __table_args__ = (
        UniqueConstraint(
            "version_id", "language_id", name="uq_program_version_language"
        ),
    )


class ProgramDocument(BaseModel):
    __tablename__ = "program_documents"

    version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("program_versions.id", ondelete="CASCADE"), index=True
    )
    document_type: Mapped[str] = mapped_column(String(50), default="other")
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    object_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    version: Mapped["ProgramVersion"] = relationship(
        "ProgramVersion", back_populates="documents"
    )
    translations: Mapped[list["ProgramDocumentTranslation"]] = relationship(
        "ProgramDocumentTranslation",
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ProgramDocumentTranslation(BaseModel):
    __tablename__ = "program_document_translations"

    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("program_documents.id", ondelete="CASCADE"), index=True
    )
    language_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("languages.id", ondelete="RESTRICT"), index=True
    )
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    document: Mapped["ProgramDocument"] = relationship(
        "ProgramDocument", back_populates="translations"
    )
    language: Mapped["Language"] = relationship("Language", lazy="joined")

    __table_args__ = (
        UniqueConstraint(
            "document_id", "language_id", name="uq_program_document_language"
        ),
    )


class ProgramOutcome(BaseModel):
    __tablename__ = "program_outcomes"

    version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("program_versions.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(30))
    outcome_type: Mapped[str] = mapped_column(String(30))
    parent_code: Mapped[str | None] = mapped_column(String(30), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    version: Mapped["ProgramVersion"] = relationship(
        "ProgramVersion", back_populates="outcomes"
    )
    translations: Mapped[list["ProgramOutcomeTranslation"]] = relationship(
        "ProgramOutcomeTranslation",
        back_populates="outcome",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint(
            "version_id", "code", "outcome_type", name="uq_program_outcome_code"
        ),
    )


class ProgramOutcomeTranslation(BaseModel):
    __tablename__ = "program_outcome_translations"

    outcome_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("program_outcomes.id", ondelete="CASCADE"), index=True
    )
    language_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("languages.id", ondelete="RESTRICT"), index=True
    )
    content: Mapped[str] = mapped_column(Text)

    outcome: Mapped["ProgramOutcome"] = relationship(
        "ProgramOutcome", back_populates="translations"
    )
    language: Mapped["Language"] = relationship("Language", lazy="joined")

    __table_args__ = (
        UniqueConstraint(
            "outcome_id", "language_id", name="uq_program_outcome_language"
        ),
    )


class ProgramCourse(BaseModel):
    __tablename__ = "program_courses"

    version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("program_versions.id", ondelete="CASCADE"), index=True
    )
    course_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    row_type: Mapped[str] = mapped_column(String(30), default="course")
    credits: Mapped[float | None] = mapped_column(Numeric(5, 1), nullable=True)
    credits_text: Mapped[str | None] = mapped_column(String(30), nullable=True)
    semester: Mapped[str | None] = mapped_column(String(30), nullable=True)
    knowledge_block: Mapped[str | None] = mapped_column(String(100), nullable=True)
    course_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    managing_unit: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    version: Mapped["ProgramVersion"] = relationship(
        "ProgramVersion", back_populates="courses"
    )
    translations: Mapped[list["ProgramCourseTranslation"]] = relationship(
        "ProgramCourseTranslation",
        back_populates="course",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("version_id", "course_code", name="uq_program_course_code"),
    )


class ProgramCourseTranslation(BaseModel):
    __tablename__ = "program_course_translations"

    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("program_courses.id", ondelete="CASCADE"), index=True
    )
    language_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("languages.id", ondelete="RESTRICT"), index=True
    )
    name: Mapped[str] = mapped_column(String(500))

    course: Mapped["ProgramCourse"] = relationship(
        "ProgramCourse", back_populates="translations"
    )
    language: Mapped["Language"] = relationship("Language", lazy="joined")

    __table_args__ = (
        UniqueConstraint("course_id", "language_id", name="uq_program_course_language"),
    )
