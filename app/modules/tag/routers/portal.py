import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.tag.schemas import PortalTagResponse
from app.modules.tag.service import tag_service
from app.shared.pagination import PaginatedResponse, PaginationParams

router = APIRouter()


@router.get("", response_model=PaginatedResponse[PortalTagResponse])
async def list_tags_portal(
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    only_has_articles: bool = Query(default=False),
    lang: str = Query(default="vi"),
    params: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[PortalTagResponse]:
    tags, total = await tag_service.list_tags(
        db, search=search, is_active=is_active, only_has_articles=only_has_articles, page=params.page, limit=params.limit, lang=lang
    )
    response_items = [PortalTagResponse.model_validate(tag) for tag in tags]
    return PaginatedResponse.create(items=response_items, total=total, params=params)


@router.get("/{tag_id}", response_model=PortalTagResponse)
async def get_tag_portal(
    tag_id: uuid.UUID,
    lang: str = Query(default="vi"),
    db: AsyncSession = Depends(get_db),
) -> PortalTagResponse:
    tag = await tag_service.get_tag_by_id(db, tag_id, lang=lang)
    return PortalTagResponse.model_validate(tag)
