import uuid
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.banner.models import BannerPosition, BannerTargetType

class TrimBaseModel(BaseModel):
    """
    Lớp BaseModel cơ sở hỗ trợ tự động trim khoảng trắng hai đầu
    cho tất cả các dữ liệu đầu vào kiểu chuỗi (string).
    """
    @field_validator("*", mode="before")
    @classmethod
    def trim_strings(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.strip()
        return v


class BannerBase(TrimBaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Tiêu đề banner")
    description: Optional[str] = Field(None, description="Mô tả chi tiết banner")
    desktop_image_object_key: str = Field(..., max_length=512, description="Object key ảnh desktop")
    mobile_image_object_key: Optional[str] = Field(None, max_length=512, description="Object key ảnh mobile")
    link_url: Optional[str] = Field(None, max_length=1000, description="Đường dẫn liên kết khi click")
    open_in_new_tab: bool = Field(False, description="Mở link trong tab mới")
    position: BannerPosition = Field(..., description="Vị trí hiển thị banner")
    sort_order: int = Field(1, ge=0, description="Thứ tự hiển thị")
    start_at: Optional[datetime] = Field(None, description="Thời gian bắt đầu hiển thị hiệu lực")
    end_at: Optional[datetime] = Field(None, description="Thời gian kết thúc hiển thị hiệu lực")
    is_active: bool = Field(True, description="Trạng thái hoạt động")
    article_id: Optional[uuid.UUID] = Field(None, description="ID bài viết liên kết tương ứng")
    target_type: BannerTargetType = Field(BannerTargetType.EXTERNAL, description="Loại liên kết của banner")


class BannerCreate(BannerBase):
    pass


class BannerUpdate(TrimBaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Tiêu đề banner")
    description: Optional[str] = Field(None, description="Mô tả chi tiết banner")
    desktop_image_object_key: Optional[str] = Field(None, max_length=512, description="Object key ảnh desktop")
    mobile_image_object_key: Optional[str] = Field(None, max_length=512, description="Object key ảnh mobile")
    link_url: Optional[str] = Field(None, max_length=1000, description="Đường dẫn liên kết khi click")
    open_in_new_tab: Optional[bool] = Field(None, description="Mở link trong tab mới")
    position: Optional[BannerPosition] = Field(None, description="Vị trí hiển thị banner")
    sort_order: Optional[int] = Field(None, ge=0, description="Thứ tự hiển thị")
    start_at: Optional[datetime] = Field(None, description="Thời gian bắt đầu hiển thị hiệu lực")
    end_at: Optional[datetime] = Field(None, description="Thời gian kết thúc hiển thị hiệu lực")
    is_active: Optional[bool] = Field(None, description="Trạng thái hoạt động")
    article_id: Optional[uuid.UUID] = Field(None, description="ID bài viết liên kết tương ứng")
    target_type: Optional[BannerTargetType] = Field(None, description="Loại liên kết của banner")


class BannerStatusUpdate(BaseModel):
    is_active: bool = Field(..., description="Trạng thái hoạt động")


class BannerResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    desktop_image_object_key: str
    mobile_image_object_key: Optional[str] = None
    link_url: Optional[str] = None
    open_in_new_tab: bool
    position: BannerPosition
    sort_order: int
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    is_active: bool
    article_id: Optional[uuid.UUID] = None
    target_type: BannerTargetType
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("desktop_image_object_key", "mobile_image_object_key")
    @classmethod
    def transform_image_url(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return v
        if v.startswith("http://") or v.startswith("https://"):
            return v
        from app.core.config import settings
        protocol = "https" if settings.MINIO_SECURE else "http"
        return f"{protocol}://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET}/{v}"
