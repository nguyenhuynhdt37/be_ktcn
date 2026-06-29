import uuid
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator


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


class PositionBase(TrimBaseModel):
    name: str = Field(..., min_length=1, max_length=150, description="Tên chức vụ tiếng Việt")
    english_name: Optional[str] = Field(None, max_length=150, description="Tên chức vụ tiếng Anh")
    description: Optional[str] = Field(None, description="Mô tả chức vụ")
    sort_order: int = Field(0, ge=0, description="Thứ tự hiển thị (phải lớn hơn hoặc bằng 0)")
    is_active: bool = Field(True, description="Trạng thái hoạt động")


class PositionCreate(PositionBase):
    pass


class PositionUpdate(TrimBaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150, description="Tên chức vụ tiếng Việt")
    english_name: Optional[str] = Field(None, max_length=150, description="Tên chức vụ tiếng Anh")
    description: Optional[str] = Field(None, description="Mô tả chức vụ")
    sort_order: Optional[int] = Field(None, ge=0, description="Thứ tự hiển thị (phải lớn hơn hoặc bằng 0)")
    is_active: Optional[bool] = Field(None, description="Trạng thái hoạt động")


class PositionStatusUpdate(BaseModel):
    is_active: bool = Field(..., description="Trạng thái hoạt động")


class PositionResponse(BaseModel):
    id: uuid.UUID
    name: str
    english_name: Optional[str] = None
    description: Optional[str] = None
    sort_order: int
    is_active: bool
    staff_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PositionPaginationResponse(BaseModel):
    items: list[PositionResponse]
    page: int = Field(..., description="Trang hiện tại (1-based)")
    page_size: int = Field(..., description="Số lượng phần tử trên mỗi trang")
    total_items: int = Field(..., description="Tổng số phần tử thỏa mãn bộ lọc")
    total_pages: int = Field(..., description="Tổng số trang")
    has_next: bool = Field(..., description="Có trang kế tiếp hay không")
    has_previous: bool = Field(..., description="Có trang trước đó hay không")


class DepartmentBase(TrimBaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Tên bộ môn tiếng Việt")
    english_name: Optional[str] = Field(None, max_length=255, description="Tên bộ môn tiếng Anh")
    description: Optional[str] = Field(None, description="Mô tả bộ môn")
    thumbnail_object_key: Optional[str] = Field(None, max_length=512, description="Ảnh đại diện bộ môn")
    phone: Optional[str] = Field(None, max_length=50, description="Số điện thoại")
    email: Optional[str] = Field(None, max_length=255, description="Email liên hệ")
    website: Optional[str] = Field(None, max_length=255, description="Website")
    office: Optional[str] = Field(None, max_length=255, description="Văn phòng làm việc")
    sort_order: int = Field(0, ge=0, description="Thứ tự hiển thị")
    is_active: bool = Field(True, description="Trạng thái hoạt động")


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(TrimBaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Tên bộ môn tiếng Việt")
    english_name: Optional[str] = Field(None, max_length=255, description="Tên bộ môn tiếng Anh")
    description: Optional[str] = Field(None, description="Mô tả bộ môn")
    thumbnail_object_key: Optional[str] = Field(None, max_length=512, description="Ảnh đại diện bộ môn")
    phone: Optional[str] = Field(None, max_length=50, description="Số điện thoại")
    email: Optional[str] = Field(None, max_length=255, description="Email liên hệ")
    website: Optional[str] = Field(None, max_length=255, description="Website")
    office: Optional[str] = Field(None, max_length=255, description="Văn phòng làm việc")
    sort_order: Optional[int] = Field(None, ge=0, description="Thứ tự hiển thị")
    is_active: Optional[bool] = Field(None, description="Trạng thái hoạt động")


class DepartmentStatusUpdate(BaseModel):
    is_active: bool = Field(..., description="Trạng thái hoạt động")


class DepartmentResponse(BaseModel):
    id: uuid.UUID
    name: str
    english_name: Optional[str] = None
    slug: str
    description: Optional[str] = None
    thumbnail_object_key: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    office: Optional[str] = None
    sort_order: int
    is_active: bool
    staff_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DepartmentPaginationResponse(BaseModel):
    items: list[DepartmentResponse]
    page: int = Field(..., description="Trang hiện tại (1-based)")
    page_size: int = Field(..., description="Số lượng phần tử trên mỗi trang")
    total_items: int = Field(..., description="Tổng số phần tử thỏa mãn bộ lọc")
    total_pages: int = Field(..., description="Tổng số trang")
    has_next: bool = Field(..., description="Có trang kế tiếp hay không")
    has_previous: bool = Field(..., description="Có trang trước đó hay không")


class DepartmentMinimal(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class PositionMinimal(BaseModel):
    id: uuid.UUID
    name: str
    sort_order: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class StaffBase(TrimBaseModel):
    department_id: uuid.UUID = Field(..., description="ID bộ môn")
    position_id: uuid.UUID = Field(..., description="ID chức vụ chính")
    full_name: str = Field(..., min_length=1, max_length=255, description="Họ và tên")
    english_name: Optional[str] = Field(None, max_length=255, description="Tên tiếng Anh")
    academic_title: Optional[str] = Field(None, max_length=50, description="Học hàm (Giáo sư, Phó Giáo sư...)")
    degree: Optional[str] = Field(None, max_length=100, description="Học vị (Tiến sĩ, Thạc sĩ...)")
    avatar_object_key: Optional[str] = Field(None, max_length=512, description="Ảnh đại diện")
    email: Optional[str] = Field(None, max_length=255, description="Email công tác")
    phone: Optional[str] = Field(None, max_length=50, description="Số điện thoại")
    website: Optional[str] = Field(None, max_length=255, description="Trang web cá nhân")
    office: Optional[str] = Field(None, max_length=255, description="Phòng làm việc")
    biography: Optional[str] = Field(None, description="Tiểu sử/Quá trình công tác")
    research_interests: Optional[str] = Field(None, description="Hướng nghiên cứu chính")
    sort_order: int = Field(0, ge=0, description="Thứ tự hiển thị")
    is_active: bool = Field(True, description="Trạng thái hoạt động")


class StaffCreate(StaffBase):
    pass


class StaffUpdate(TrimBaseModel):
    department_id: Optional[uuid.UUID] = Field(None, description="ID bộ môn")
    position_id: Optional[uuid.UUID] = Field(None, description="ID chức vụ chính")
    full_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Họ và tên")
    english_name: Optional[str] = Field(None, max_length=255, description="Tên tiếng Anh")
    academic_title: Optional[str] = Field(None, max_length=50, description="Học hàm")
    degree: Optional[str] = Field(None, max_length=100, description="Học vị")
    avatar_object_key: Optional[str] = Field(None, max_length=512, description="Ảnh đại diện")
    email: Optional[str] = Field(None, max_length=255, description="Email công tác")
    phone: Optional[str] = Field(None, max_length=50, description="Số điện thoại")
    website: Optional[str] = Field(None, max_length=255, description="Trang web cá nhân")
    office: Optional[str] = Field(None, max_length=255, description="Phòng làm việc")
    biography: Optional[str] = Field(None, description="Tiểu sử/Quá trình công tác")
    research_interests: Optional[str] = Field(None, description="Hướng nghiên cứu chính")
    sort_order: Optional[int] = Field(None, ge=0, description="Thứ tự hiển thị")
    is_active: Optional[bool] = Field(None, description="Trạng thái hoạt động")


class StaffStatusUpdate(BaseModel):
    is_active: bool = Field(..., description="Trạng thái hoạt động")


class StaffResponse(BaseModel):
    id: uuid.UUID
    department_id: uuid.UUID
    position_id: uuid.UUID
    full_name: str
    english_name: Optional[str] = None
    slug: str
    academic_title: Optional[str] = None
    degree: Optional[str] = None
    avatar_object_key: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    office: Optional[str] = None
    biography: Optional[str] = None
    research_interests: Optional[str] = None
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    department: Optional[DepartmentMinimal] = None
    position: Optional[PositionMinimal] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("avatar_object_key")
    @classmethod
    def transform_avatar_url(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return v
        if v.startswith("http://") or v.startswith("https://"):
            return v
        from app.core.config import settings
        protocol = "https" if settings.MINIO_SECURE else "http"
        return f"{protocol}://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET}/{v}"


class StaffPaginationResponse(BaseModel):
    items: list[StaffResponse]
    page: int = Field(..., description="Trang hiện tại (1-based)")
    page_size: int = Field(..., description="Số lượng phần tử trên mỗi trang")
    total_items: int = Field(..., description="Tổng số phần tử thỏa mãn bộ lọc")
    total_pages: int = Field(..., description="Tổng số trang")
    has_next: bool = Field(..., description="Có trang kế tiếp hay không")
    has_previous: bool = Field(..., description="Có trang trước đó hay không")


class DepartmentStatsResponse(BaseModel):
    total: int = Field(..., description="Tổng số bộ môn hiện có (kể cả active và inactive)")
    active: int = Field(..., description="Số bộ môn đang hoạt động (is_active = true)")
    inactive: int = Field(..., description="Số bộ môn không hoạt động (is_active = false)")
    total_staff: int = Field(..., description="Tổng số nhân sự/giảng viên đang sinh hoạt tại tất cả bộ môn")


class PositionStatsResponse(BaseModel):
    total: int = Field(..., description="Tổng số chức vụ hiện có")
    active: int = Field(..., description="Số chức vụ đang hoạt động (is_active = true)")
    inactive: int = Field(..., description="Số chức vụ không hoạt động (is_active = false)")
    total_staff: int = Field(..., description="Tổng số nhân sự đang được gán các chức vụ này")


class StaffStatsResponse(BaseModel):
    total: int = Field(..., description="Tổng số giảng viên trong danh sách")
    active: int = Field(..., description="Số giảng viên đang công tác/hoạt động (is_active = true)")
    inactive: int = Field(..., description="Số giảng viên không hoạt động (is_active = false)")
    high_qualification: int = Field(..., description="Số lượng giảng viên trình độ cao: Học vị Tiến sĩ (TS) hoặc Học hàm PGS/GS")


