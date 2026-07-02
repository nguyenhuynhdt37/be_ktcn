import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.position.schemas import PortalPositionResponse
from app.modules.position.service import position_service

portal_router = APIRouter()


@portal_router.get("", response_model=list[PortalPositionResponse])
async def list_positions_portal(
    accept_language: Optional[str] = Header(None, alias="Accept-Language"),
    lang: Optional[str] = Query(None, description="Mã ngôn ngữ (vi, en)"),
    db: AsyncSession = Depends(get_db),
) -> list[PortalPositionResponse]:
    """
    [Portal Website] Lấy danh sách tất cả các chức vụ đã dịch và làm phẳng (chỉ trả về active).
    """
    selected_lang = "vi"
    if lang:
        selected_lang = lang
    elif accept_language:
        primary = accept_language.split(",")[0].split("-")[0].lower()
        if primary in ["vi", "en"]:
            selected_lang = primary

    positions, _ = await position_service.list_positions(
        db=db,
        is_active=True,
        sort_by="sort_order",
        order="asc",
        page=1,
        page_size=1000,
        lang=selected_lang,
    )
    return [PortalPositionResponse.model_validate(p) for p in positions]
