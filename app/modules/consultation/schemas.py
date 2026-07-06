import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.consultation.models import ConsultationRequestType, ConsultationStatus


class ConsultationCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=9, max_length=20)
    email: str = Field(min_length=5, max_length=255)
    interested_major: str = Field(min_length=2, max_length=255)
    request_type: ConsultationRequestType
    message: str | None = Field(default=None, max_length=2000)
    consent_given: bool
    website: str | None = Field(default=None, max_length=200)

    @field_validator(
        "full_name", "email", "interested_major", "message", "website", mode="before"
    )
    @classmethod
    def trim_strings(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        normalized = re.sub(r"[\s().-]", "", value)
        if normalized.startswith("+84"):
            normalized = "0" + normalized[3:]
        if not re.fullmatch(r"0\d{9,10}", normalized):
            raise ValueError("Số điện thoại không đúng định dạng Việt Nam")
        return normalized

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized):
            raise ValueError("Email không đúng định dạng")
        return normalized

    @model_validator(mode="after")
    def validate_consent_and_honeypot(self) -> "ConsultationCreate":
        if not self.consent_given:
            raise ValueError("Bạn cần đồng ý chính sách sử dụng dữ liệu")
        if self.website:
            raise ValueError("Yêu cầu không hợp lệ")
        return self


class ConsultationCreatedResponse(BaseModel):
    id: uuid.UUID
    reference_code: str
    status: ConsultationStatus
    created_at: datetime
    message: str = "Yêu cầu tư vấn đã được tiếp nhận"

    model_config = ConfigDict(from_attributes=True)


class ConsultationAdminResponse(BaseModel):
    id: uuid.UUID
    reference_code: str
    full_name: str
    phone: str
    email: str
    interested_major: str
    request_type: ConsultationRequestType
    message: str | None = None
    status: ConsultationStatus
    assigned_to_id: uuid.UUID | None = None
    admin_notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConsultationPaginationResponse(BaseModel):
    items: list[ConsultationAdminResponse]
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool


class ConsultationUpdate(BaseModel):
    status: ConsultationStatus | None = None
    assigned_to_id: uuid.UUID | None = None
    note: str | None = Field(default=None, min_length=1, max_length=2000)

    @field_validator("note", mode="before")
    @classmethod
    def trim_note(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


# Alias to resolve import references in routers and tests
ConsultationResponse = ConsultationAdminResponse
