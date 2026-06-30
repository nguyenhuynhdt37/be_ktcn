import uuid
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from app.core.config import settings


class LanguageCreate(BaseModel):
    """
    Schema nhận dữ liệu đầu vào khi tạo mới một ngôn ngữ.
    """
    code: str = Field(
        ...,
        min_length=1,
        max_length=10,
        pattern=r"^[a-z]+$",
        description="Mã ngôn ngữ (ví dụ: vi, en, lo), chỉ chứa chữ thường a-z, độ dài tối đa 10 ký tự"
    )
    name: str = Field(..., min_length=1, max_length=100, description="Tên tiếng Anh hoặc tên hiển thị chung của ngôn ngữ")
    native_name: str = Field(..., min_length=1, max_length=100, description="Tên bản địa của ngôn ngữ")
    flag_id: Optional[uuid.UUID] = Field(default=None, description="ID ảnh quốc kỳ trong thư viện Media")
    is_default: bool = Field(default=False, description="Đánh dấu là ngôn ngữ mặc định")
    is_system: bool = Field(default=False, description="Đánh dấu ngôn ngữ hệ thống cốt lõi")
    is_active: bool = Field(default=True, description="Trạng thái hoạt động")
    sort_order: int = Field(default=0, ge=0, description="Thứ tự sắp xếp, phải >= 0")

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        if not v.islower():
            raise ValueError("Mã ngôn ngữ chỉ được chứa chữ cái thường (a-z)")
        return v.strip()


class LanguageUpdate(BaseModel):
    """
    Schema nhận dữ liệu cập nhật thông tin ngôn ngữ.
    """
    name: Optional[str] = Field(default=None, min_length=1, max_length=100, description="Tên ngôn ngữ")
    native_name: Optional[str] = Field(default=None, min_length=1, max_length=100, description="Tên bản địa")
    flag_id: Optional[uuid.UUID] = Field(default=None, description="ID ảnh quốc kỳ trong thư viện Media")
    is_default: Optional[bool] = Field(default=None, description="Đánh dấu là ngôn ngữ mặc định")
    is_active: Optional[bool] = Field(default=None, description="Trạng thái hoạt động")
    sort_order: Optional[int] = Field(default=None, ge=0, description="Thứ tự sắp xếp, phải >= 0")


class LanguageResponse(BaseModel):
    """
    Schema phản hồi thông tin ngôn ngữ đầy đủ phục vụ quản trị (Admin).
    """
    id: uuid.UUID
    code: str
    name: str
    native_name: str
    flag_id: Optional[uuid.UUID] = None
    flag_url: Optional[str] = None
    is_default: bool
    is_system: bool
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_flag_url(cls, data: Any) -> Any:
        if not data:
            return data
        
        # 1. Nếu data là dict
        if isinstance(data, dict):
            flag = data.get("flag")
            if flag and getattr(flag, "object_key", None):
                protocol = "https" if settings.MINIO_SECURE else "http"
                data["flag_url"] = f"{protocol}://{settings.MINIO_ENDPOINT}/{getattr(flag, 'bucket', None) or settings.MINIO_BUCKET}/{getattr(flag, 'object_key', None)}"
            return data
        
        # 2. Nếu data là ORM model
        db_dict = {
            "id": getattr(data, "id", None),
            "code": getattr(data, "code", None),
            "name": getattr(data, "name", None),
            "native_name": getattr(data, "native_name", None),
            "flag_id": getattr(data, "flag_id", None),
            "is_default": getattr(data, "is_default", False),
            "is_system": getattr(data, "is_system", False),
            "is_active": getattr(data, "is_active", True),
            "sort_order": getattr(data, "sort_order", 0),
            "created_at": getattr(data, "created_at", None),
            "updated_at": getattr(data, "updated_at", None),
            "deleted_at": getattr(data, "deleted_at", None),
        }
        flag = getattr(data, "flag", None)
        if flag and getattr(flag, "object_key", None):
            protocol = "https" if settings.MINIO_SECURE else "http"
            db_dict["flag_url"] = f"{protocol}://{settings.MINIO_ENDPOINT}/{getattr(flag, 'bucket', None) or settings.MINIO_BUCKET}/{getattr(flag, 'object_key', None)}"
        else:
            db_dict["flag_url"] = None
        return db_dict


class PortalLanguageResponse(BaseModel):
    """
    Schema phản hồi thông tin ngôn ngữ tối giản phục vụ Public Portal.
    """
    id: uuid.UUID
    code: str
    name: str
    native_name: str
    flag_id: Optional[uuid.UUID] = None
    flag_url: Optional[str] = None
    is_default: bool

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_flag_url(cls, data: Any) -> Any:
        if not data:
            return data
        
        # 1. Nếu data là dict
        if isinstance(data, dict):
            flag = data.get("flag")
            if flag and getattr(flag, "object_key", None):
                protocol = "https" if settings.MINIO_SECURE else "http"
                data["flag_url"] = f"{protocol}://{settings.MINIO_ENDPOINT}/{getattr(flag, 'bucket', None) or settings.MINIO_BUCKET}/{getattr(flag, 'object_key', None)}"
            return data
        
        # 2. Nếu data là ORM model
        db_dict = {
            "id": getattr(data, "id", None),
            "code": getattr(data, "code", None),
            "name": getattr(data, "name", None),
            "native_name": getattr(data, "native_name", None),
            "flag_id": getattr(data, "flag_id", None),
            "is_default": getattr(data, "is_default", False),
        }
        flag = getattr(data, "flag", None)
        if flag and getattr(flag, "object_key", None):
            protocol = "https" if settings.MINIO_SECURE else "http"
            db_dict["flag_url"] = f"{protocol}://{settings.MINIO_ENDPOINT}/{getattr(flag, 'bucket', None) or settings.MINIO_BUCKET}/{getattr(flag, 'object_key', None)}"
        else:
            db_dict["flag_url"] = None
        return db_dict


class LanguageReorderItem(BaseModel):
    """Một item thay đổi vị trí sắp xếp kéo thả."""
    id: uuid.UUID
    sort_order: int = Field(..., ge=0, description="Mức sắp xếp mới (phải >= 0)")


class LanguageReorderRequest(BaseModel):
    """Request batch update kéo thả cấu trúc danh sách phẳng ngôn ngữ."""
    items: list[LanguageReorderItem] = Field(
        ..., min_length=1, description="Danh sách các ngôn ngữ cần sắp xếp lại"
    )
