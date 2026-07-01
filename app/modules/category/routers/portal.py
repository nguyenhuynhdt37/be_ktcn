import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.language import get_locale_from_request
from app.modules.category.schemas import (
    PortalCategoryResponse,
    PortalCategoryTreeNode,
)
from app.modules.category.service import category_service
from app.modules.article.schemas import PortalArticlePaginationResponse, PortalArticleResponse
from app.modules.article.service import article_service

portal_router = APIRouter()


@portal_router.get("/tree", response_model=list[PortalCategoryTreeNode])
async def get_category_tree_portal(
    request: Request,
    with_article_count: bool = Query(default=False, description="Bật thống kê số lượng bài viết đã xuất bản"),
    only_has_articles: bool = Query(default=False, description="Chỉ lấy cây danh mục có chứa bài viết đã xuất bản"),
    lang: Optional[str] = Query(default=None, description="Mã ngôn ngữ (vi, en)"),
    language: Optional[str] = Query(default=None, description="Bí danh của lang"),
    db: AsyncSession = Depends(get_db),
) -> list[PortalCategoryTreeNode]:
    """
    [Portal Website] Lấy cây danh mục bài viết đã làm phẳng theo ngôn ngữ hiện tại của Client (qua Accept-Language header hoặc query params).
    """
    resolved_lang = get_locale_from_request(request, lang, language)
    tree = await category_service.get_category_tree(db, with_article_count=with_article_count, only_has_articles=only_has_articles, lang=resolved_lang)
    return [PortalCategoryTreeNode.model_validate(node) for node in tree]


@portal_router.get("/{category_id}", response_model=PortalCategoryResponse)
async def get_category_portal(
    request: Request,
    category_id: uuid.UUID,
    lang: Optional[str] = Query(default=None, description="Mã ngôn ngữ (vi, en)"),
    language: Optional[str] = Query(default=None, description="Bí danh của lang"),
    db: AsyncSession = Depends(get_db),
) -> PortalCategoryResponse:
    """
    [Portal Website] Lấy chi tiết thông tin một danh mục làm phẳng theo ngôn ngữ hiện tại của Client (qua Accept-Language header hoặc query params).
    """
    resolved_lang = get_locale_from_request(request, lang, language)
    category = await category_service.get_category_by_id(db, category_id, lang=resolved_lang)
    return PortalCategoryResponse.model_validate(category)


@portal_router.get("/{category_slug}/articles", response_model=PortalArticlePaginationResponse)
async def list_category_articles_portal(
    category_slug: str,
    page: int = Query(default=1, ge=1, description="Chỉ số trang (bắt đầu từ 1)"),
    page_size: int = Query(default=10, ge=1, le=100, alias="page_size", description="Số lượng bài viết trên mỗi trang"),
    db: AsyncSession = Depends(get_db),
) -> PortalArticlePaginationResponse:
    """
    [Portal Website] Lấy danh sách các bài viết thuộc danh mục chỉ định qua slug.
    """
    items, total = await article_service.list_articles_portal(
        db,
        category_slug=category_slug,
        page=page,
        page_size=page_size
    )

    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    has_next = page < total_pages
    has_previous = page > 1

    return PortalArticlePaginationResponse(
        items=[PortalArticleResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=has_next,
        has_previous=has_previous
    )
