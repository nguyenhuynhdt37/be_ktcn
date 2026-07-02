import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.modules.article.schemas import (
    PortalArticleListResponse,
    PortalArticleResponse,
    PortalArticlePaginationResponse
)
from app.modules.article.service import article_service

router = APIRouter()


@router.get("", response_model=PortalArticlePaginationResponse)
async def list_all_articles_portal(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    search: Optional[str] = Query(default=None),
    category_slug: Optional[str] = Query(default=None),
    tag_slug: Optional[str] = Query(default=None),
    author_username: Optional[str] = Query(default=None),
    is_featured: Optional[bool] = Query(default=None),
    is_pinned: Optional[bool] = Query(default=None),
    has_thumbnail: Optional[bool] = Query(default=None),
    published_from: Optional[datetime] = Query(default=None),
    published_to: Optional[datetime] = Query(default=None),
    sort_by: str = Query(default="publish_at"),
    sort_dir: str = Query(default="desc"),
    lang: str = Query(default="vi"),
    db: AsyncSession = Depends(get_db),
) -> PortalArticlePaginationResponse:
    allowed_sort_fields = {
        "title", "slug", "created_at", "updated_at", 
        "publish_at", "published_at", "view_count", 
        "sort_order", "is_featured", "is_pinned"
    }
    if sort_by not in allowed_sort_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Trường sắp xếp 'sort_by' không hợp lệ. Cho phép: {', '.join(allowed_sort_fields)}"
        )

    if sort_dir.lower() not in {"asc", "desc"}:
        raise HTTPException(
            status_code=400,
            detail="Hướng sắp xếp 'sort_dir' chỉ được phép là 'asc' hoặc 'desc'"
        )

    items, total = await article_service.list_all_articles_portal(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        category_slug=category_slug,
        tag_slug=tag_slug,
        author_username=author_username,
        is_featured=is_featured,
        is_pinned=is_pinned,
        has_thumbnail=has_thumbnail,
        published_from=published_from,
        published_to=published_to,
        sort_by=sort_by,
        sort_dir=sort_dir,
        lang=lang,
    )

    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    has_next = page < total_pages
    has_previous = page > 1

    return PortalArticlePaginationResponse(
        items=[PortalArticleListResponse.model_validate(item) for item in items],
        page=page,
        page_size=page_size,
        total_items=total,
        total_pages=total_pages,
        has_next=has_next,
        has_previous=has_previous,
    )


@router.get("/{slug}", response_model=PortalArticleResponse)
async def get_article_detail_portal(
    slug: str,
    lang: str = Query(default="vi"),
    db: AsyncSession = Depends(get_db)
) -> PortalArticleResponse:
    article = await article_service.get_article_by_slug_portal(db, slug=slug, lang=lang)
    return PortalArticleResponse.model_validate(article)
