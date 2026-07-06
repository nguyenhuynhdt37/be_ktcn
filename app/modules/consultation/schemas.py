import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

from app.modules.consultation.models import ConsultationStatus


class ConsultationCreate(BaseModel):
    """
    Schema gửi lên từ Portal để đăng ký tư vấn.
    """
    full_name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=8, max_length=20)
    email: Optional[EmailStr] = None
    interested_major: str = Field(..., min_length=2, max_length=255)
    request_type: str = Field("ADMISSION_CONSULTING")
    message: Optional[str] = Field(None, max_length=2000)
    consent_given: bool
    website: Optional[str] = None  # Honeypot field để chống bot


class ConsultationUpdate(BaseModel):
    """
    Schema cập nhật từ Admin.
    """
    status: Optional[ConsultationStatus] = None
    notes: Optional[str] = None
    assigned_to: Optional[uuid.UUID] = None


class UserMinResponse(BaseModel):
    """
    Schema hiển thị thông tin tối giản của admin được phân công.
    """
    id: uuid.UUID
    username: str
    full_name: str

    class Config:
        from_attributes = True


class ConsultationResponse(BaseModel):
    """
    Schema phản hồi thông tin yêu cầu tư vấn.
    """
    id: uuid.UUID
    request_code: str
    fullname: str
    phone: str
    email: Optional[str] = None
    notes: Optional[str] = None
    status: ConsultationStatus
    assigned_to: Optional[uuid.UUID] = None
    assignee: Optional[UserMinResponse] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConsultationPaginationResponse(BaseModel):
    """
    Phân trang danh sách tư vấn tuyển sinh.
    """
    items: list[ConsultationResponse]
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool
