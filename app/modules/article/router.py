import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserResponse
from app.modules.article.models import ArticleStatus
from app.modules.article.schemas import (
    ArticleListResponse,
    ArticlePaginationResponse,
    BulkStatusUpdateRequest,
    BulkActionResponse,
    ArticleStatsResponse,
    ArticleAttributesUpdateRequest,
    ArticleCreateRequest,
    SlugCheckResponse,
    ArticleDetailResponse,
    ArticleDraftsCountResponse,
    ArticleUpdateRequest,
    PortalArticleDetailResponse,
)
from app.modules.article.service import article_service

router = APIRouter()


@router.get("", response_model=ArticlePaginationResponse)
async def list_articles(
    page: int = Query(default=1, ge=1, description="Chỉ số trang (bắt đầu từ 1)"),
    page_size: int = Query(default=10, ge=1, le=100, alias="page_size", description="Số lượng bài viết trên mỗi trang"),
    search: Optional[str] = Query(default=None, description="Tìm kiếm theo tiêu đề hoặc slug"),
    category_id: Optional[uuid.UUID] = Query(default=None, description="Lọc theo ID danh mục"),
    author_id: Optional[uuid.UUID] = Query(default=None, description="Lọc theo ID tác giả"),
    tag_ids: Optional[list[str]] = Query(default=None, alias="tag_ids", description="Lọc theo danh sách ID thẻ tag"),
    tag_ids_arr: Optional[list[str]] = Query(default=None, alias="tag_ids[]", description="Lọc theo danh sách ID thẻ tag (dạng mảng array[])"),
    status: Optional[ArticleStatus] = Query(default=None, description="Lọc theo trạng thái (PUBLISHED, SCHEDULED, ARCHIVED)"),
    is_featured: Optional[bool] = Query(default=None, description="Lọc bài viết nổi bật"),
    is_pinned: Optional[bool] = Query(default=None, description="Lọc bài viết ghim"),
    is_draft: Optional[bool] = Query(default=False, description="Lọc bài viết nháp (True = Bản nháp, False = Bài viết chính thức)"),
    created_from: Optional[datetime] = Query(default=None, description="Lọc thời gian tạo từ"),
    created_to: Optional[datetime] = Query(default=None, description="Lọc thời gian tạo đến"),
    published_from: Optional[datetime] = Query(default=None, description="Lọc thời gian xuất bản từ"),
    published_to: Optional[datetime] = Query(default=None, description="Lọc thời gian xuất bản đến"),
    deleted: bool = Query(default=False, description="Lọc trạng thái xóa mềm (True = trong thùng rác, False = bình thường)"),
    sort_by: str = Query(default="created_at", description="Trường sắp xếp (title, created_at, updated_at, published_at, view_count, sort_order)"),
    sort_dir: str = Query(default="desc", description="Hướng sắp xếp (asc, desc)"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ArticlePaginationResponse:
    """
    Lấy danh sách các bài viết với phân trang, lọc và sắp xếp động.
    
    Yêu cầu trạng thái:
    - Chỉ cho phép lấy các bài viết có trạng thái: **PUBLISHED**, **SCHEDULED**, **ARCHIVED**.
    - **DRAFT** không được phép hiển thị qua API này (sẽ báo lỗi hoặc tự lọc bỏ qua).
    """
    # Validation sort_by
    allowed_sort_fields = {"title", "created_at", "updated_at", "published_at", "view_count", "sort_order"}
    if sort_by not in allowed_sort_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Trường sắp xếp 'sort_by' không hợp lệ. Cho phép: {', '.join(allowed_sort_fields)}"
        )

    # Validation sort_dir
    if sort_dir.lower() not in {"asc", "desc"}:
        raise HTTPException(
            status_code=400,
            detail="Hướng sắp xếp 'sort_dir' chỉ được phép là 'asc' hoặc 'desc'"
        )

    # Validation status
    if status and status == ArticleStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail="Không cho phép truy vấn trạng thái DRAFT qua API này."
        )

    # Phân tích cú pháp tag_ids (hỗ trợ cả tag_ids, tag_ids[] và chuỗi phân tách bởi dấu phẩy)
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
                        raise HTTPException(
                            status_code=400,
                            detail=f"ID tag '{sub_item}' không phải là UUID hợp lệ."
                        )
        else:
            item = item.strip()
            if item:
                try:
                    parsed_tag_ids.append(uuid.UUID(item))
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail=f"ID tag '{item}' không phải là UUID hợp lệ."
                    )

    # Gọi service
    items, total = await article_service.list_articles(
        db,
        page=page,
        page_size=page_size,
        search=search,
        category_id=category_id,
        author_id=author_id,
        tag_ids=parsed_tag_ids or None,
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
    )

    # Tính toán pagination
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    has_next = page < total_pages
    has_previous = page > 1

    # Format response
    response_items = [ArticleListResponse.model_validate(item) for item in items]

    return ArticlePaginationResponse(
        items=response_items,
        page=page,
        page_size=page_size,
        total_items=total,
        total_pages=total_pages,
        has_next=has_next,
        has_previous=has_previous,
    )


@router.get("/drafts", response_model=ArticlePaginationResponse)
async def list_my_drafts(
    page: int = Query(default=1, ge=1, description="Chỉ số trang (bắt đầu từ 1)"),
    page_size: int = Query(default=10, ge=1, le=100, alias="page_size", description="Số lượng bài viết nháp trên mỗi trang"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ArticlePaginationResponse:
    """
    Lấy danh sách các bài viết nháp (DRAFT) của chính tác giả đang đăng nhập.
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
    
    response_items = [ArticleListResponse.model_validate(item) for item in items]
    return ArticlePaginationResponse(
        items=response_items,
        page=page,
        page_size=page_size,
        total_items=total,
        total_pages=total_pages,
        has_next=has_next,
        has_previous=has_previous
    )


@router.get("/drafts/count", response_model=ArticleDraftsCountResponse)
async def count_my_drafts(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ArticleDraftsCountResponse:
    """
    Đếm số lượng bài viết nháp (DRAFT) của chính tác giả đang đăng nhập.
    """
    count = await article_service.count_my_drafts(db, current_user=current_user)
    return ArticleDraftsCountResponse(count=count)


@router.get("/check-slug", response_model=SlugCheckResponse)
async def check_slug_availability(
    slug: str = Query(..., description="Slug cần kiểm tra tính khả dụng"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SlugCheckResponse:
    """
    Kiểm tra xem một slug đã tồn tại hay chưa, và gợi ý slug mới nếu bị trùng.
    """
    return await article_service.check_slug_availability(db, slug=slug)


@router.get("/stats", response_model=ArticleStatsResponse)
async def get_article_stats(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ArticleStatsResponse:
    """
    Lấy thống kê nhanh về số lượng bài viết theo các trạng thái và tổng lượt xem trong tháng.
    """
    return await article_service.get_article_stats(db)


@router.post("/bulk-status", response_model=BulkActionResponse)
async def bulk_update_status(
    payload: BulkStatusUpdateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BulkActionResponse:
    """
    Cập nhật trạng thái hàng loạt cho danh sách bài viết.
    
    Hành động được hỗ trợ:
    - **archive**: Chuyển các bài viết PUBLISHED sang ARCHIVED.
    - **publish**: Chuyển các bài viết ARCHIVED sang PUBLISHED.
    - **delete**: Xóa mềm (Soft Delete) bài viết.
    - **restore**: Khôi phục bài viết bị xóa mềm trong thùng rác.
    """
    return await article_service.bulk_update_status(
        db,
        article_ids=payload.article_ids,
        action=payload.action,
        current_user=current_user
    )


@router.patch("/{article_id}/archive", response_model=ArticleListResponse)
async def archive_article(
    article_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ArticleListResponse:
    """
    Chuyển bài viết đã xuất bản (PUBLISHED) sang trạng thái Lưu trữ (ARCHIVED).
    
    Quy tắc nghiệp vụ:
    - Chỉ cho phép archive nếu bài viết hiện tại có trạng thái là **PUBLISHED**.
    - Nếu bài viết ở trạng thái **DRAFT** hoặc **SCHEDULED**, hệ thống sẽ trả về lỗi **400 Bad Request**.
    """
    article = await article_service.archive_article(
        db,
        article_id=article_id,
        current_user=current_user
    )
    return ArticleListResponse.model_validate(article)


@router.patch("/{article_id}/publish", response_model=ArticleListResponse)
async def publish_article(
    article_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ArticleListResponse:
    """
    Khôi phục bài viết đã lưu trữ (ARCHIVED) quay trở lại trạng thái công khai (PUBLISHED).
    
    Quy tắc nghiệp vụ:
    - Chỉ cho phép publish nếu bài viết hiện tại đang có trạng thái lưu trữ là **ARCHIVED**.
    - Nếu bài viết ở trạng thái **DRAFT** hoặc **SCHEDULED**, hệ thống sẽ trả về lỗi **400 Bad Request**.
    """
    article = await article_service.publish_article(
        db,
        article_id=article_id,
        current_user=current_user
    )
    return ArticleListResponse.model_validate(article)


@router.patch("/{article_id}/attributes", response_model=ArticleListResponse)
async def update_article_attributes(
    article_id: uuid.UUID,
    payload: ArticleAttributesUpdateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ArticleListResponse:
    """
    Bật/Tắt nhanh các thuộc tính đặc biệt (is_featured, is_pinned) của bài viết.
    """
    article = await article_service.update_article_attributes(
        db,
        article_id=article_id,
        payload=payload,
        current_user=current_user
    )
    return ArticleListResponse.model_validate(article)


@router.post("", response_model=ArticleListResponse, status_code=status.HTTP_201_CREATED)
async def create_article(
    payload: ArticleCreateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ArticleListResponse:
    """
    Tạo bài viết mới.
    """
    article = await article_service.create_article(
        db,
        payload=payload,
        current_user=current_user
    )
    return ArticleListResponse.model_validate(article)


@router.get("/{article_id}", response_model=ArticleDetailResponse)
async def get_article_detail(
    article_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ArticleDetailResponse:
    """
    Lấy thông tin chi tiết bài viết theo ID (chứa content và SEO settings).
    Áp dụng phân quyền draft security.
    """
    article = await article_service.get_article_detail(
        db,
        article_id=article_id,
        current_user=current_user
    )
    return ArticleDetailResponse.model_validate(article)


@router.put("/{article_id}", response_model=ArticleListResponse)
async def update_article(
    article_id: uuid.UUID,
    payload: ArticleUpdateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ArticleListResponse:
    """
    Cập nhật toàn bộ bài viết (bao gồm cả trạng thái nháp, danh mục, tags, SEO...).
    Áp dụng phân quyền draft security.
    """
    article = await article_service.update_article(
        db,
        article_id=article_id,
        payload=payload,
        current_user=current_user
    )
    return ArticleListResponse.model_validate(article)


@router.get("/portal/{slug}", response_model=PortalArticleDetailResponse)
async def get_article_detail_portal(
    slug: str,
    db: AsyncSession = Depends(get_db)
) -> PortalArticleDetailResponse:
    """
    Lấy chi tiết thông tin bài viết công khai theo slug cho Portal FE Client (Public API).
    Hỗ trợ đếm lượt xem (view_count) tự động và cấu trúc siêu dữ liệu SEO/OpenGraph/JSON-LD.
    """
    article = await article_service.get_article_by_slug_portal(db, slug=slug)
    return PortalArticleDetailResponse.model_validate(article)
