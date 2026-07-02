import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.department.schemas import PortalDepartmentResponse
from app.modules.department.service import department_service

portal_router = APIRouter()


@portal_router.get("", response_model=list[PortalDepartmentResponse])
async def list_departments_portal(
    accept_language: Optional[str] = Header(None, alias="Accept-Language"),
    lang: Optional[str] = Query(None, description="Mã ngôn ngữ (vi, en)"),
    db: AsyncSession = Depends(get_db),
) -> list[PortalDepartmentResponse]:
    """
    [Portal Website] Lấy danh sách bộ môn đã dịch và làm phẳng (chỉ trả về bộ môn active).
    """
    # Quyết định mã ngôn ngữ ưu tiên
    selected_lang = "vi"
    if lang:
        selected_lang = lang
    elif accept_language:
        # Lấy ngôn ngữ đầu tiên trong chuỗi Accept-Language
        primary = accept_language.split(",")[0].split("-")[0].lower()
        if primary in ["vi", "en"]:
            selected_lang = primary

    departments, _ = await department_service.list_departments(
        db=db,
        is_active=True,
        sort_by="sort_order",
        order="asc",
        page=1,
        page_size=1000,
        lang=selected_lang,
    )
    return [PortalDepartmentResponse.model_validate(d) for d in departments]


@portal_router.get("/{slug}", response_model=PortalDepartmentResponse)
async def get_department_by_slug_portal(
    slug: str,
    accept_language: Optional[str] = Header(None, alias="Accept-Language"),
    lang: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> PortalDepartmentResponse:
    """
    [Portal Website] Lấy chi tiết bộ môn theo slug.
    """
    selected_lang = "vi"
    if lang:
        selected_lang = lang
    elif accept_language:
        primary = accept_language.split(",")[0].split("-")[0].lower()
        if primary in ["vi", "en"]:
            selected_lang = primary

    dept = await department_service.get_department_by_slug(db, slug, lang=selected_lang)
    if not dept.is_active:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Không tìm thấy bộ môn")
    return PortalDepartmentResponse.model_validate(dept)
