import uuid
from typing import Optional
from pydantic import BaseModel, Field, field_validator


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


class LanguageReorderItem(BaseModel):
    """Một item thay đổi vị trí sắp xếp kéo thả."""
    id: uuid.UUID
    sort_order: int = Field(..., ge=0, description="Mức sắp xếp mới (phải >= 0)")


class LanguageReorderRequest(BaseModel):
    """Request batch update kéo thả cấu trúc danh sách phẳng ngôn ngữ."""
    items: list[LanguageReorderItem] = Field(
        ..., min_length=1, description="Danh sách các ngôn ngữ cần sắp xếp lại"
    )
