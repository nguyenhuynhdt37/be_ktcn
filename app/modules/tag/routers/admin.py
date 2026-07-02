import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Request, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.audit.service import log_action
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserResponse
from app.modules.tag.schemas import TagCreate, AdminTagResponse, TagStatusUpdate, TagUpdate
from app.modules.tag.service import tag_service
from app.shared.pagination import PaginatedResponse, PaginationParams

router = APIRouter()


@router.get("", response_model=PaginatedResponse[AdminTagResponse])
async def list_tags(
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    only_has_articles: bool = Query(default=False),
    lang: str = Query(default="vi"),
    params: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[AdminTagResponse]:
    tags, total = await tag_service.list_tags(
        db, search=search, is_active=is_active, only_has_articles=only_has_articles, page=params.page, limit=params.limit, lang=lang
    )
    response_items = [AdminTagResponse.model_validate(tag) for tag in tags]
    return PaginatedResponse.create(items=response_items, total=total, params=params)


@router.get("/{tag_id}", response_model=AdminTagResponse)
async def get_tag(
    tag_id: uuid.UUID,
    lang: str = Query(default="vi"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AdminTagResponse:
    tag = await tag_service.get_tag_by_id(db, tag_id, lang=lang)
    return AdminTagResponse.model_validate(tag)


def _get_tag_log_data(tag, default_name: str = "Tag") -> dict:
    trans = None
    for t in getattr(tag, "translations", []):
        if t.language and t.language.code == "vi":
            trans = t
            break
    if not trans and getattr(tag, "translations", []):
        trans = tag.translations[0]
    if trans:
        return {"name": trans.name, "slug": trans.slug}
    return {"name": default_name, "slug": ""}


@router.post("", response_model=AdminTagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    request: Request,
    payload: TagCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AdminTagResponse:
    tag = await tag_service.create_tag(db, payload)
    
    await log_action(
        db,
        current_user,
        "TAG_CREATED",
        "tag",
        tag.id,
        _get_tag_log_data(tag),
        request,
    )
    await db.commit()
    return AdminTagResponse.model_validate(tag)


@router.put("/{tag_id}", response_model=AdminTagResponse)
async def update_tag(
    request: Request,
    tag_id: uuid.UUID,
    payload: TagUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AdminTagResponse:
    tag = await tag_service.update_tag(db, tag_id, payload)
    
    await log_action(
        db,
        current_user,
        "TAG_UPDATED",
        "tag",
        tag.id,
        _get_tag_log_data(tag),
        request,
    )
    await db.commit()
    return AdminTagResponse.model_validate(tag)


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    request: Request,
    tag_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    tag = await tag_service.get_tag_by_id(db, tag_id)
    await tag_service.delete_tag(db, tag_id)
    
    await log_action(
        db,
        current_user,
        "TAG_DELETED",
        "tag",
        tag_id,
        _get_tag_log_data(tag),
        request,
    )
    await db.commit()


@router.patch("/{tag_id}/status", response_model=AdminTagResponse)
async def toggle_tag_status(
    request: Request,
    tag_id: uuid.UUID,
    payload: TagStatusUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AdminTagResponse:
    tag = await tag_service.toggle_tag_status(db, tag_id, payload.is_active)
    
    await log_action(
        db,
        current_user,
        "TAG_STATUS_TOGGLED",
        "tag",
        tag.id,
        {"name": _get_tag_log_data(tag)["name"], "is_active": tag.is_active},
        request,
    )
    await db.commit()
    return AdminTagResponse.model_validate(tag)
