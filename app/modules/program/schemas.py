import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProgramTranslationInput(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str | None = None
    short_description: str | None = None
    description: str | None = None
    career_opportunities: str | None = None
    admissions_info: str | None = None


class ProgramCreate(BaseModel):
    department_id: uuid.UUID
    code: str | None = None
    degree_level: str = "bachelor"
    duration_years: float | None = None
    training_mode: str | None = None
    thumbnail_object_key: str | None = None
    sort_order: int = 0
    is_active: bool = True
    is_published: bool = False
    translations: dict[str, ProgramTranslationInput]

    @field_validator("code", mode="before")
    @classmethod
    def empty_code(cls, value: Any) -> Any:
        return value or None


class ProgramUpdate(BaseModel):
    department_id: uuid.UUID | None = None
    code: str | None = None
    degree_level: str | None = None
    duration_years: float | None = None
    training_mode: str | None = None
    thumbnail_object_key: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None
    is_published: bool | None = None
    translations: dict[str, ProgramTranslationInput] | None = None


class ProgramResponse(BaseModel):
    id: uuid.UUID
    department_id: uuid.UUID
    code: str | None = None
    degree_level: str
    duration_years: float | None = None
    training_mode: str | None = None
    thumbnail_object_key: str | None = None
    sort_order: int
    is_active: bool
    is_published: bool
    name: str = ""
    slug: str = ""
    short_description: str | None = None
    description: str | None = None
    career_opportunities: str | None = None
    admissions_info: str | None = None
    translations: dict[str, Any] = {}
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ProgramPaginationResponse(BaseModel):
    items: list[ProgramResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class LocalizedVersionInput(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    summary: str | None = None
    general_objective: str | None = None
    career_opportunities: str | None = None


class LocalizedDocumentInput(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str | None = None


class LocalizedContentInput(BaseModel):
    content: str = Field(min_length=1)


class LocalizedCourseInput(BaseModel):
    name: str = Field(min_length=1, max_length=500)


class ProgramDocumentInput(BaseModel):
    document_type: str = Field(default="other", max_length=50)
    source_url: str | None = None
    object_key: str | None = Field(default=None, max_length=512)
    mime_type: str | None = Field(default=None, max_length=100)
    file_size: int | None = Field(default=None, ge=0)
    page_count: int | None = Field(default=None, ge=0)
    checksum_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    sort_order: int = 0
    translations: dict[str, LocalizedDocumentInput]


class ProgramOutcomeInput(BaseModel):
    code: str = Field(min_length=1, max_length=30)
    outcome_type: str = Field(pattern="^(objective|learning_outcome)$")
    parent_code: str | None = Field(default=None, max_length=30)
    sort_order: int = 0
    translations: dict[str, LocalizedContentInput]


class ProgramCourseInput(BaseModel):
    course_code: str | None = Field(default=None, max_length=50)
    row_type: str = Field(
        default="course", pattern="^(course|group|placeholder|summary)$"
    )
    credits: float | None = Field(default=None, ge=0)
    credits_text: str | None = Field(default=None, max_length=30)
    semester: str | None = Field(default=None, max_length=30)
    knowledge_block: str | None = Field(default=None, max_length=100)
    course_type: str | None = Field(default=None, max_length=50)
    managing_unit: str | None = Field(default=None, max_length=255)
    sort_order: int = 0
    translations: dict[str, LocalizedCourseInput]


class ProgramVersionInput(BaseModel):
    version_year: int = Field(ge=1900, le=2200)
    cohort_code: str | None = Field(default=None, max_length=50)
    total_credits: float | None = Field(default=None, ge=0)
    is_current: bool = False
    is_published: bool = True
    sort_order: int = 0
    translations: dict[str, LocalizedVersionInput]
    documents: list[ProgramDocumentInput] = Field(default_factory=list)
    outcomes: list[ProgramOutcomeInput] = Field(default_factory=list)
    courses: list[ProgramCourseInput] = Field(default_factory=list)


class ProgramAcademicProfileInput(BaseModel):
    versions: list[ProgramVersionInput]

    @field_validator("versions")
    @classmethod
    def validate_versions(
        cls, versions: list[ProgramVersionInput]
    ) -> list[ProgramVersionInput]:
        years = [version.version_year for version in versions]
        if len(years) != len(set(years)):
            raise ValueError("Mỗi năm chỉ được có một phiên bản chương trình")
        if sum(version.is_current for version in versions) > 1:
            raise ValueError("Chỉ được chọn một phiên bản hiện hành")
        return versions


class ProgramDocumentResponse(BaseModel):
    id: uuid.UUID
    document_type: str
    title: str = ""
    description: str | None = None
    source_url: str | None = None
    file_url: str | None = None
    mime_type: str | None = None
    file_size: int | None = None
    page_count: int | None = None
    checksum_sha256: str | None = None
    sort_order: int


class ProgramOutcomeResponse(BaseModel):
    id: uuid.UUID
    code: str
    outcome_type: str
    parent_code: str | None = None
    content: str = ""
    sort_order: int


class ProgramCourseResponse(BaseModel):
    id: uuid.UUID
    course_code: str | None = None
    row_type: str
    name: str = ""
    credits: float | None = None
    credits_text: str | None = None
    semester: str | None = None
    knowledge_block: str | None = None
    course_type: str | None = None
    managing_unit: str | None = None
    sort_order: int


class ProgramVersionResponse(BaseModel):
    id: uuid.UUID
    version_year: int
    cohort_code: str | None = None
    total_credits: float | None = None
    is_current: bool
    is_published: bool
    sort_order: int
    title: str = ""
    summary: str | None = None
    general_objective: str | None = None
    career_opportunities: str | None = None
    documents: list[ProgramDocumentResponse] = Field(default_factory=list)
    objectives: list[ProgramOutcomeResponse] = Field(default_factory=list)
    learning_outcomes: list[ProgramOutcomeResponse] = Field(default_factory=list)
    courses: list[ProgramCourseResponse] = Field(default_factory=list)


class ProgramDetailResponse(ProgramResponse):
    versions: list[ProgramVersionResponse] = Field(default_factory=list)
