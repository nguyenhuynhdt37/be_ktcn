import uuid
from datetime import datetime
from typing import Optional, Any
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserResponse
from app.modules.article.models import ArticleStatus
from app.modules.article.schemas import (
    ArticleCreateRequest,
    ArticleUpdateRequest,
    AdminArticleResponse,
    BulkStatusUpdateRequest,
    BulkActionResponse,
    ArticleStatsResponse,
    ArticleAttributesUpdateRequest,
    SlugCheckResponse,
    ArticleDraftsCountResponse,
    ArticleSEOAnalyzeRequest,
    ArticleSEOAnalyzeResponse,
    ArticleSEORewriteRequest,
    ArticleSEORewriteResponse,
    ArticleGenerateByIdeaRequest,
    ArticleGenerateByIdeaResponse,
    ArticleSummaryRequest,
    ArticleSummaryResponse,
)
from app.modules.article.service import article_service

router = APIRouter()


class AdminArticlePaginationResponse(AdminArticleResponse.__base__ or object):
    pass


from pydantic import BaseModel, Field

class ArticlePaginationResponse(BaseModel):
    items: list[AdminArticleResponse]
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool


@router.get("", response_model=ArticlePaginationResponse)
async def list_articles(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    search: Optional[str] = Query(default=None),
    category_id: Optional[uuid.UUID] = Query(default=None),
    author_id: Optional[uuid.UUID] = Query(default=None),
    tag_ids: Optional[list[str]] = Query(default=None, alias="tag_ids"),
    tag_ids_arr: Optional[list[str]] = Query(default=None, alias="tag_ids[]"),
    status: Optional[ArticleStatus] = Query(default=None),
    is_featured: Optional[bool] = Query(default=None),
    is_pinned: Optional[bool] = Query(default=None),
    is_draft: Optional[bool] = Query(default=False),
    created_from: Optional[datetime] = Query(default=None),
    created_to: Optional[datetime] = Query(default=None),
    published_from: Optional[datetime] = Query(default=None),
    published_to: Optional[datetime] = Query(default=None),
    deleted: bool = Query(default=False),
    sort_by: str = Query(default="created_at"),
    sort_dir: str = Query(default="desc"),
    lang: str = Query(default="vi"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ArticlePaginationResponse:
    allowed_sort_fields = {"title", "created_at", "updated_at", "published_at", "view_count", "sort_order"}
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

    if status and status == ArticleStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail="Không cho phép truy vấn trạng thái DRAFT qua API này."
        )

    parsed_tag_ids = []
    raw_tags = []
    if tag_ids:
        raw_tags.extend(tag_ids)
    if tag_ids_arr:
        raw_tags.extend(tag_ids_arr)

    for item in raw_tags:
        if "," in item:
            for sub_item in item.split(","):
                sub_item = sub_item.strip()
                if sub_item:
                    try:
                        parsed_tag_ids.append(uuid.UUID(sub_item))
                    except ValueError:
                        pass
        else:
            try:
                parsed_tag_ids.append(uuid.UUID(item))
            except ValueError:
                pass

    items, total = await article_service.list_articles(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        category_id=category_id,
        author_id=author_id,
        tag_ids=parsed_tag_ids if parsed_tag_ids else None,
        status=status,
        is_featured=is_featured,
        is_pinned=is_pinned,
        is_draft=is_draft,
        created_from=created_from,
        created_to=created_to,
        published_from=published_from,
        published_to=published_to,
        deleted=deleted,
        sort_by=sort_by,
        sort_dir=sort_dir,
        lang=lang
    )

    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    has_next = page < total_pages
    has_previous = page > 1

    return ArticlePaginationResponse(
        items=[AdminArticleResponse.model_validate(item) for item in items],
        page=page,
        page_size=page_size,
        total_items=total,
        total_pages=total_pages,
        has_next=has_next,
        has_previous=has_previous,
    )


@router.post("", response_model=AdminArticleResponse, status_code=status.HTTP_201_CREATED)
async def create_article(
    payload: ArticleCreateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AdminArticleResponse:
    article = await article_service.create_article(
        db,
        payload=payload,
        current_user=current_user
    )
    return AdminArticleResponse.model_validate(article)


@router.get("/drafts/count", response_model=ArticleDraftsCountResponse)
async def get_my_drafts_count(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ArticleDraftsCountResponse:
    count = await article_service.count_my_drafts(db, current_user=current_user)
    return ArticleDraftsCountResponse(count=count)


@router.get("/drafts", response_model=ArticlePaginationResponse)
async def list_my_drafts(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ArticlePaginationResponse:
    """
    Lấy danh sách các bài viết nháp của chính tác giả đang đăng nhập (phân trang).
    """
    items, total = await article_service.list_my_drafts(
        db,
        current_user=current_user,
        page=page,
        page_size=page_size
    )
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    has_next = page < total_pages
    has_previous = page > 1

    return ArticlePaginationResponse(
        items=[AdminArticleResponse.model_validate(item) for item in items],
        page=page,
        page_size=page_size,
        total_items=total,
        total_pages=total_pages,
        has_next=has_next,
        has_previous=has_previous,
    )


@router.get("/stats", response_model=ArticleStatsResponse)
async def get_article_stats(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ArticleStatsResponse:
    return await article_service.get_article_stats(db)


@router.put("/bulk-status", response_model=BulkActionResponse)
async def bulk_status_update(
    payload: BulkStatusUpdateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> BulkActionResponse:
    return await article_service.bulk_update_status(
        db,
        article_ids=payload.article_ids,
        action=payload.action,
        current_user=current_user
    )


@router.get("/check-slug", response_model=SlugCheckResponse)
async def check_slug_availability(
    slug: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db)
) -> SlugCheckResponse:
    return await article_service.check_slug_availability(db, slug=slug)


@router.get("/{article_id}", response_model=AdminArticleResponse)
async def get_article_detail(
    article_id: uuid.UUID,
    lang: str = Query(default="vi"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AdminArticleResponse:
    article = await article_service.get_article_detail(
        db,
        article_id=article_id,
        current_user=current_user,
        lang=lang
    )
    return AdminArticleResponse.model_validate(article)


@router.put("/{article_id}", response_model=AdminArticleResponse)
async def update_article(
    article_id: uuid.UUID,
    payload: ArticleUpdateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AdminArticleResponse:
    article = await article_service.update_article(
        db,
        article_id=article_id,
        payload=payload,
        current_user=current_user
    )
    return AdminArticleResponse.model_validate(article)


@router.patch("/{article_id}/attributes", response_model=AdminArticleResponse)
async def update_article_attributes(
    article_id: uuid.UUID,
    payload: ArticleAttributesUpdateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AdminArticleResponse:
    article = await article_service.update_article_attributes(
        db,
        article_id=article_id,
        payload=payload,
        current_user=current_user
    )
    return AdminArticleResponse.model_validate(article)


@router.patch("/{article_id}/archive", response_model=AdminArticleResponse)
async def archive_article(
    article_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AdminArticleResponse:
    article = await article_service.archive_article(
        db,
        article_id=article_id,
        current_user=current_user
    )
    return AdminArticleResponse.model_validate(article)


@router.patch("/{article_id}/publish", response_model=AdminArticleResponse)
async def publish_article(
    article_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AdminArticleResponse:
    article = await article_service.publish_article(
        db,
        article_id=article_id,
        current_user=current_user
    )
    return AdminArticleResponse.model_validate(article)


@router.post("/{article_id}/restore", response_model=AdminArticleResponse)
async def restore_article(
    article_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AdminArticleResponse:
    article = await article_service.restore_article(
        db,
        article_id=article_id,
        current_user=current_user
    )
    return AdminArticleResponse.model_validate(article)


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(
    article_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await article_service.delete_article(db, article_id=article_id, current_user=current_user)


@router.post("/{article_id}/seo/analyze", response_model=ArticleSEOAnalyzeResponse)
async def analyze_article_seo(
    article_id: uuid.UUID,
    payload: ArticleSEOAnalyzeRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ArticleSEOAnalyzeResponse:
    """
    Thực hiện phân tích SEO cho bài viết (Rule Engine & AI suggestions).
    Hỗ trợ truyền dữ liệu thay đổi trên form chưa lưu trong payload.
    """
    from app.modules.article.seo_service import seo_service
    return await seo_service.analyze_article(
        db=db,
        article_id=article_id,
        payload=payload,
        current_user=current_user
    )


@router.post("/{article_id}/seo/rewrite", response_model=ArticleSEORewriteResponse)
async def rewrite_article_content(
    article_id: uuid.UUID,
    payload: ArticleSEORewriteRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ArticleSEORewriteResponse:
    """
    Sử dụng AI viết lại nội dung bài viết theo văn phong và từ khóa chính, bảo toàn ảnh base64.
    """
    from app.modules.article.seo_service import seo_service
    return await seo_service.rewrite_article(
        db=db,
        payload=payload,
        current_user=current_user
    )


@router.post("/seo/generate-by-idea", response_model=ArticleGenerateByIdeaResponse)
async def generate_article_by_idea(
    payload: ArticleGenerateByIdeaRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ArticleGenerateByIdeaResponse:
    """
    Sử dụng AI tự động soạn thảo toàn bộ bài viết (Tiêu đề, Tóm tắt, HTML Content, Slug, SEO Title, SEO Desc) từ mô tả ý tưởng/dàn ý của người dùng.
    """
    from app.modules.article.seo_service import seo_service
    return await seo_service.generate_by_idea(
        db=db,
        payload=payload,
        current_user=current_user
    )


@router.post("/{article_id}/seo/summarize", response_model=ArticleSummaryResponse)
async def summarize_article_content(
    article_id: uuid.UUID,
    payload: ArticleSummaryRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ArticleSummaryResponse:
    """
    Sử dụng AI tự động tóm tắt bài viết dạng text thuần túy (không HTML) để điền vào phần tóm tắt (excerpt).
    """
    from app.modules.article.seo_service import seo_service
    return await seo_service.summarize_article(
        db=db,
        payload=payload,
        current_user=current_user
    )


