import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.language import get_locale_from_request
from app.modules.menu.schemas import (
    PortalMenuTreeResponse,
)
from app.modules.menu.service import menu_service

portal_router = APIRouter()


@portal_router.get("/{code}/tree", response_model=PortalMenuTreeResponse)
async def get_menu_tree_portal(
    request: Request,
    code: str,
    lang: Optional[str] = Query(default=None, description="Mã ngôn ngữ (vi, en)"),
    language: Optional[str] = Query(default=None, description="Bí danh của lang"),
    db: AsyncSession = Depends(get_db),
) -> PortalMenuTreeResponse:
    """
    [Portal Website] Lấy cây menu đệ quy làm phẳng theo ngôn ngữ hiện tại của Client (qua Accept-Language header hoặc query params).
    """
    resolved_lang = get_locale_from_request(request, lang, language)
    tree = await menu_service.get_menu_tree_by_code(db, code, lang=resolved_lang)
    return PortalMenuTreeResponse.model_validate(tree)
