import uuid
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, model_validator, Field
from app.modules.department.schemas.common import build_department_resolved


class AdminDepartmentResponse(BaseModel):
    """Response thông tin Bộ môn phục vụ quản trị."""
    id: uuid.UUID
    thumbnail_object_key: Optional[str] = None
    logo_object_key: Optional[str] = None
    banner_object_key: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    office: Optional[str] = None
    sort_order: int
    display_order: Optional[int] = None
    is_active: bool
    head_staff_id: Optional[uuid.UUID] = None
    is_translated: dict[str, bool] = {}
    translations: dict[str, Any] = {}
    name: str = ""
    description: Optional[str] = None
    slug: str = ""
    staff_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_department_before_validation(cls, data: Any) -> Any:
        return build_department_resolved(data)


class DepartmentPaginationResponse(BaseModel):
    """Response phân trang danh sách bộ môn."""
    items: list[AdminDepartmentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class DepartmentStatsResponse(BaseModel):
    total: int
    active: int
    inactive: int


class DepartmentSEOAnalyzeRequest(BaseModel):
    name: Optional[str] = Field(default=None, description="Tên khoa/bộ môn hiện tại trên form")
    description: Optional[str] = Field(default=None, description="Mô tả giới thiệu khoa hiện tại trên form")
    mission: Optional[str] = Field(default=None, description="Sứ mệnh hiện tại trên form (HTML)")
    vision: Optional[str] = Field(default=None, description="Tầm nhìn hiện tại trên form (HTML)")
    history: Optional[str] = Field(default=None, description="Lịch sử hiện tại trên form (HTML)")
    research_overview: Optional[str] = Field(default=None, description="Tổng quan nghiên cứu hiện tại trên form (HTML)")
    seo_title: Optional[str] = Field(default=None, description="Tiêu đề SEO hiện tại trên form")
    seo_description: Optional[str] = Field(default=None, description="Mô tả SEO hiện tại trên form")
    focus_keyword: Optional[str] = Field(default=None, description="Từ khóa chính phân tích")
    thumbnail_object_key: Optional[str] = Field(default=None, description="Thumbnail")
    logo_object_key: Optional[str] = Field(default=None, description="Logo")
    banner_object_key: Optional[str] = Field(default=None, description="Banner")
    slug: Optional[str] = Field(default=None, description="Slug")
    lang: str = Field(default="vi", description="Ngôn ngữ phân tích (mặc định: vi)")

