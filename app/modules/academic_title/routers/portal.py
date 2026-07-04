from typing import List
from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.academic_title.schemas.portal import AcademicTitlePortalResponse
from app.modules.academic_title.service import AcademicTitleService

portal_router = APIRouter()

academic_title_service = AcademicTitleService()


@portal_router.get("", response_model=List[AcademicTitlePortalResponse])
async def list_academic_titles_portal(
    lang: str = "vi",
    accept_language: str = Header(None, alias="Accept-Language"),
    db: AsyncSession = Depends(get_db),
):
    """Lấy danh sách Học hàm hoạt động phẳng (đã dịch) cho Portal Website."""
    preferred_lang = lang
    if accept_language and not lang:
        first_lang = accept_language.split(",")[0].split(";")[0].split("-")[0].strip().lower()
        if first_lang in ["vi", "en"]:
            preferred_lang = first_lang

    return await academic_title_service.list_academic_titles(
        db, is_active=True, lang=preferred_lang
    )
