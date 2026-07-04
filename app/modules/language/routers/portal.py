from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.language.schemas import PortalLanguageResponse
from app.modules.language.service import language_service

portal_router = APIRouter()


@portal_router.get("", response_model=list[PortalLanguageResponse])
async def list_portal_languages(
    db: AsyncSession = Depends(get_db),
) -> list[PortalLanguageResponse]:
    """
    Lấy danh sách các ngôn ngữ đang hoạt động của hệ thống (Public API).
    Chỉ trả về các thông tin cơ bản: id, code, name, native_name, is_default.
    """
    languages = await language_service.list_portal_languages(db)
    return [PortalLanguageResponse.model_validate(lang) for lang in languages]
