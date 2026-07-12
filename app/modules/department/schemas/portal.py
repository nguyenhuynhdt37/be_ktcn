import uuid
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, model_validator
from app.modules.department.schemas.common import build_department_resolved
from app.modules.program.schemas import ProgramResponse
from app.modules.gallery.schemas import GalleryResponse
from app.modules.article.schemas.portal import PortalArticleListResponse


class PortalDepartmentListResponse(BaseModel):
    """Response thông tin Bộ môn rút gọn cho trang Danh sách (không kèm trường HTML nặng)."""
    id: uuid.UUID
    code: Optional[str] = None
    unit_type: str
    thumbnail_object_key: Optional[str] = None
    logo_object_key: Optional[str] = None
    banner_object_key: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    office: Optional[str] = None
    sort_order: int
    display_order: Optional[int] = None
    head_staff_id: Optional[uuid.UUID] = None
    name: str = ""
    description: Optional[str] = None
    slug: str = ""
    staff_count: int = 0

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_department_before_validation(cls, data: Any) -> Any:
        return build_department_resolved(data)


class PortalDepartmentResponse(PortalDepartmentListResponse):
    """Response chi tiết Bộ môn đầy đủ (có kèm các trường HTML sứ mệnh, lịch sử...)."""
    mission: Optional[str] = None
    vision: Optional[str] = None
    history: Optional[str] = None
    research_overview: Optional[str] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None



class DepartmentStaffSummary(BaseModel):
    id: uuid.UUID
    full_name: str
    slug: str
    avatar_object_key: Optional[str] = None
    academic_title: Optional[str] = None
    degree: Optional[str] = None
    position_name: Optional[str] = None
    biography: Optional[str] = None
    research_interests: Optional[str] = None


class DepartmentOverviewStats(BaseModel):
    staff_count: int
    doctorate_count: int
    associate_professor_count: int


class PortalDepartmentOverviewResponse(BaseModel):
    department: PortalDepartmentResponse
    staffs: list[DepartmentStaffSummary]
    stats: DepartmentOverviewStats
    programs: list[ProgramResponse] = []
    latest_articles: list[PortalArticleListResponse] = []
    galleries: list[GalleryResponse] = []
