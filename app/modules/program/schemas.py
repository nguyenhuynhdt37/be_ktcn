import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProgramTranslationInput(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: Optional[str] = None
    short_description: Optional[str] = None
    description: Optional[str] = None
    career_opportunities: Optional[str] = None
    admissions_info: Optional[str] = None


class ProgramCreate(BaseModel):
    department_id: uuid.UUID
    code: Optional[str] = None
    degree_level: str = "bachelor"
    duration_years: Optional[float] = None
    training_mode: Optional[str] = None
    thumbnail_object_key: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True
    is_published: bool = False
    translations: dict[str, ProgramTranslationInput]

    @field_validator("code", mode="before")
    @classmethod
    def empty_code(cls, value: Any) -> Any:
        return value or None


class ProgramUpdate(BaseModel):
    department_id: Optional[uuid.UUID] = None
    code: Optional[str] = None
    degree_level: Optional[str] = None
    duration_years: Optional[float] = None
    training_mode: Optional[str] = None
    thumbnail_object_key: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    is_published: Optional[bool] = None
    translations: Optional[dict[str, ProgramTranslationInput]] = None


class ProgramResponse(BaseModel):
    id: uuid.UUID
    department_id: uuid.UUID
    code: Optional[str] = None
    degree_level: str
    duration_years: Optional[float] = None
    training_mode: Optional[str] = None
    thumbnail_object_key: Optional[str] = None
    sort_order: int
    is_active: bool
    is_published: bool
    name: str = ""
    slug: str = ""
    short_description: Optional[str] = None
    description: Optional[str] = None
    career_opportunities: Optional[str] = None
    admissions_info: Optional[str] = None
    translations: dict[str, Any] = {}
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ProgramPaginationResponse(BaseModel):
    items: list[ProgramResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
