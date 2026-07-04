from typing import List
from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.degree.schemas import DegreePortalResponse
from app.modules.degree.service import DegreeService

portal_router = APIRouter()
degree_service = DegreeService()


@portal_router.get("", response_model=List[DegreePortalResponse])
async def list_degrees_portal(
    lang: str = "vi",
    accept_language: str = Header(None, alias="Accept-Language"),
    db: AsyncSession = Depends(get_db)
):
    """Lấy danh sách Học vị hoạt động phẳng (đã dịch) cho Portal Website."""
    # Xác định ngôn ngữ ưu tiên
    preferred_lang = lang
    if accept_language and not lang:
        # Parse Accept-Language cơ bản (ví dụ: en-US,en;q=0.9 -> en)
        first_lang = accept_language.split(",")[0].split(";")[0].split("-")[0].strip().lower()
        if first_lang in ["vi", "en"]:
            preferred_lang = first_lang

    return await degree_service.list_degrees(
        db, is_active=True, lang=preferred_lang
    )
