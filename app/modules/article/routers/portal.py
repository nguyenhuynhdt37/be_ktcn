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
    category_slugs: Optional[list[str]] = Query(default=None, alias="category_slugs"),
    category_slugs_arr: Optional[list[str]] = Query(default=None, alias="category_slugs[]"),
    exclude_category_slugs: Optional[list[str]] = Query(default=None, alias="exclude_category_slugs"),
    exclude_category_slugs_arr: Optional[list[str]] = Query(default=None, alias="exclude_category_slugs[]"),
    tag_slug: Optional[str] = Query(default=None),
    author_username: Optional[str] = Query(default=None),
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
        "sort_order", "is_pinned"
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

    parsed_category_slugs = []
    raw_slugs = []
    if category_slugs:
        raw_slugs.extend(category_slugs)
    if category_slugs_arr:
        raw_slugs.extend(category_slugs_arr)

    for item in raw_slugs:
        if "," in item:
            for sub_item in item.split(","):
                sub_item = sub_item.strip()
                if sub_item:
                    parsed_category_slugs.append(sub_item)
        else:
            item = item.strip()
            if item:
                parsed_category_slugs.append(item)

    parsed_exclude_category_slugs = []
    raw_exclude_slugs = []
    if exclude_category_slugs:
        raw_exclude_slugs.extend(exclude_category_slugs)
    if exclude_category_slugs_arr:
        raw_exclude_slugs.extend(exclude_category_slugs_arr)

    for item in raw_exclude_slugs:
        if "," in item:
            for sub_item in item.split(","):
                sub_item = sub_item.strip()
                if sub_item:
                    parsed_exclude_category_slugs.append(sub_item)
        else:
            item = item.strip()
            if item:
                parsed_exclude_category_slugs.append(item)

    items, total = await article_service.list_all_articles_portal(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        category_slug=category_slug,
        category_slugs=parsed_category_slugs if parsed_category_slugs else None,
        exclude_category_slugs=parsed_exclude_category_slugs if parsed_exclude_category_slugs else None,
        tag_slug=tag_slug,
        author_username=author_username,
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
