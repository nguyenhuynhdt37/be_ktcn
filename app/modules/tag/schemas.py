import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TagCreate(BaseModel):
    """
    Schema nhận dữ liệu đầu vào khi tạo mới một Tag.
    """
    name: str = Field(..., min_length=1, max_length=100, description="Tên Tag")
    slug: Optional[str] = Field(
        default=None,
        max_length=100,
        pattern=r"^[a-z0-9-]+$",
        description="Đường dẫn SEO, tự sinh từ name nếu bỏ trống (chỉ chứa chữ thường, số, gạch ngang)"
    )
    description: Optional[str] = Field(default=None, description="Mô tả chi tiết Tag")
    color: Optional[str] = Field(
        default=None,
        max_length=7,
        pattern=r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$",
        description="Mã màu HEX đại diện cho Tag, ví dụ: #FF5733"
    )
    sort_order: int = Field(default=0, description="Thứ tự sắp xếp")
    is_active: bool = Field(default=True, description="Trạng thái hoạt động")

    @field_validator("slug", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: str | None) -> str | None:
        if v == "":
            return None
        if isinstance(v, str):
            return v.lower().strip()
        return v


class TagUpdate(BaseModel):
    """
    Schema nhận dữ liệu cập nhật một Tag.
    """
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    slug: Optional[str] = Field(default=None, max_length=100, pattern=r"^[a-z0-9-]+$")
    description: Optional[str] = None
    color: Optional[str] = Field(
        default=None,
        max_length=7,
        pattern=r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$"
    )
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None

    @field_validator("slug", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: str | None) -> str | None:
        if v == "":
            return None
        if isinstance(v, str):
            return v.lower().strip()
        return v


class TagResponse(BaseModel):
    """
    Schema trả thông tin Tag cho API client.
    """
    id: uuid.UUID
    name: str
    slug: str
    description: Optional[str] = None
    color: Optional[str] = None
    usage_count: int
    article_count: int = 0
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TagStatusUpdate(BaseModel):
    """
    Schema để cập nhật trạng thái hoạt động (bật/tắt).
    """
    is_active: bool = Field(..., description="Trạng thái hoạt động (True = Bật, False = Tắt)")
