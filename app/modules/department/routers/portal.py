import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.modules.department.schemas import PortalDepartmentResponse, PortalDepartmentOverviewResponse
from app.modules.department.service import department_service

portal_router = APIRouter()


def resolve_language(accept_language: Optional[str], lang: Optional[str]) -> str:
    if lang in ["vi", "en"]:
        return lang
    if accept_language:
        primary = accept_language.split(",")[0].split("-")[0].lower()
        if primary in ["vi", "en"]:
            return primary
    return "vi"


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


@portal_router.get("/{slug}/overview", response_model=PortalDepartmentOverviewResponse)
async def get_department_overview_portal(
    slug: str,
    accept_language: Optional[str] = Header(None, alias="Accept-Language"),
    lang: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> PortalDepartmentOverviewResponse:
    """Return the public department profile and its published staff roster."""
    selected_lang = resolve_language(accept_language, lang)
    department = await department_service.get_department_by_slug(db, slug, lang=selected_lang)
    if not department.is_active:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Không tìm thấy đơn vị")

    from app.modules.staff.service import staff_service

    staffs, _ = await staff_service.list_staffs(
        db=db,
        department_id=department.id,
        is_active=True,
        is_visible=True,
        sort_by="sort_order",
        order="asc",
        page=1,
        page_size=1000,
        lang=selected_lang,
    )
    doctorate_count = sum(1 for staff in staffs if (staff.degree_resolved or "").lower() in ["tiến sĩ", "doctorate"])
    associate_professor_count = sum(
        1 for staff in staffs if (staff.academic_title_resolved or "").lower() in ["phó giáo sư", "associate professor"]
    )
    department.staff_count = len(staffs)
    protocol = "https" if settings.MINIO_SECURE else "http"

    def avatar_url(value: Optional[str]) -> Optional[str]:
        if not value or value.startswith(("http://", "https://", "data:")):
            return value
        return f"{protocol}://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET}/{value}"

    staff_summaries = [
        {
            "id": staff.id,
            "full_name": staff.full_name,
            "slug": staff.slug,
            "avatar_object_key": avatar_url(staff.avatar_object_key),
            "academic_title": staff.academic_title_resolved,
            "degree": staff.degree_resolved,
            "position_name": getattr(staff.position, "name", None),
            "biography": staff.biography,
            "research_interests": staff.research_interests,
        }
        for staff in staffs
    ]
    from app.modules.program.routers import response as program_response
    from app.modules.program.service import program_service
    from app.modules.gallery.routers import response as gallery_response
    from app.modules.gallery.service import gallery_service
    from app.modules.article.schemas.portal import PortalArticleListResponse
    from app.modules.article.service import article_service

    programs, _ = await program_service.list(
        db, department_id=department.id, published_only=True, page_size=100, lang=selected_lang
    )
    galleries, _ = await gallery_service.list(
        db, department_id=department.id, active_only=True, page_size=20, lang=selected_lang
    )
    articles, _ = await article_service.list_all_articles_portal(
        db=db, department_id=department.id, page=1, page_size=6, lang=selected_lang
    )
    return PortalDepartmentOverviewResponse(
        department=PortalDepartmentResponse.model_validate(department),
        staffs=staff_summaries,
        stats={
            "staff_count": len(staffs),
            "doctorate_count": doctorate_count,
            "associate_professor_count": associate_professor_count,
        },
        programs=[program_response(item) for item in programs],
        latest_articles=[PortalArticleListResponse.model_validate(item) for item in articles],
        galleries=[gallery_response(item) for item in galleries],
    )


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
