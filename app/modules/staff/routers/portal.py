import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.staff.schemas import PortalStaffResponse
from app.modules.staff.service import staff_service

portal_router = APIRouter()


@portal_router.get("", response_model=list[PortalStaffResponse])
async def list_staffs_portal(
    department_id: Optional[uuid.UUID] = Query(None, description="Lọc theo bộ môn"),
    department_slug: Optional[str] = Query(None, description="Lọc theo slug bộ môn"),
    position_id: Optional[uuid.UUID] = Query(None, description="Lọc theo chức vụ"),
    accept_language: Optional[str] = Header(None, alias="Accept-Language"),
    lang: Optional[str] = Query(None, description="Mã ngôn ngữ (vi, en)"),
    db: AsyncSession = Depends(get_db),
) -> list[PortalStaffResponse]:
    """
    [Portal Website] Lấy danh sách giảng viên đã dịch và làm phẳng (chỉ trả về active).
    """
    selected_lang = "vi"
    if lang:
        selected_lang = lang
    elif accept_language:
        primary = accept_language.split(",")[0].split("-")[0].lower()
        if primary in ["vi", "en"]:
            selected_lang = primary

    if department_slug:
        from app.modules.department.service import department_service
        try:
            dept = await department_service.get_department_by_slug(db, department_slug, lang=selected_lang)
            department_id = dept.id
        except Exception:
            return []

    staffs, _ = await staff_service.list_staffs(
        db=db,
        department_id=department_id,
        position_id=position_id,
        is_active=True,
        sort_by="sort_order",
        order="asc",
        page=1,
        page_size=1000,
        lang=selected_lang,
    )
    return [PortalStaffResponse.model_validate(s) for s in staffs]


@portal_router.get("/{slug}", response_model=PortalStaffResponse)
async def get_staff_by_slug_portal(
    slug: str,
    accept_language: Optional[str] = Header(None, alias="Accept-Language"),
    lang: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> PortalStaffResponse:
    """
    [Portal Website] Lấy chi tiết hồ sơ giảng viên theo slug.
    """
    selected_lang = "vi"
    if lang:
        selected_lang = lang
    elif accept_language:
        primary = accept_language.split(",")[0].split("-")[0].lower()
        if primary in ["vi", "en"]:
            selected_lang = primary

    staff = await staff_service.get_staff_by_slug(db, slug, lang=selected_lang)
    if not staff.is_active:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Không tìm thấy giảng viên")
    return PortalStaffResponse.model_validate(staff)
