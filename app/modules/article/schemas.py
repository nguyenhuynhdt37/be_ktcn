import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.article.models import ArticleStatus


class ArticleCategoryListResponse(BaseModel):
    """
    Thông tin danh mục rút gọn phục vụ hiển thị danh sách bài viết.
    """
    id: uuid.UUID
    name: str
    slug: str

    model_config = ConfigDict(from_attributes=True)


class ArticleTagListResponse(BaseModel):
    """
    Thông tin Tag rút gọn phục vụ hiển thị danh sách bài viết.
    """
    id: uuid.UUID
    name: str
    slug: str
    color: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ArticleAuthorListResponse(BaseModel):
    """
    Thông tin tác giả rút gọn phục vụ hiển thị danh sách bài viết (kèm hình đại diện).
    """
    id: uuid.UUID
    username: str
    full_name: str
    avatar_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_avatar_url(cls, data: Any) -> Any:
        from app.core.config import settings
        protocol = "https" if settings.MINIO_SECURE else "http"
        
        # 1. Trường hợp data là đối tượng SQLAlchemy User
        if hasattr(data, "avatar") and data.avatar:
            avatar_url = f"{protocol}://{settings.MINIO_ENDPOINT}/{data.avatar.bucket or settings.MINIO_BUCKET}/{data.avatar.object_key}"
            data.avatar_url = avatar_url
        elif hasattr(data, "avatar_url") and data.avatar_url:
            v = data.avatar_url
            if not (v.startswith("http://") or v.startswith("https://")):
                data.avatar_url = f"{protocol}://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET}/{v}"
        
        # 2. Trường hợp data là dict (ví dụ FE gửi/test)
        elif isinstance(data, dict):
            avatar = data.get("avatar")
            if avatar and isinstance(avatar, dict) and avatar.get("object_key"):
                bucket = avatar.get("bucket") or settings.MINIO_BUCKET
                data["avatar_url"] = f"{protocol}://{settings.MINIO_ENDPOINT}/{bucket}/{avatar['object_key']}"
            elif data.get("avatar_url"):
                v = data["avatar_url"]
                if not (v.startswith("http://") or v.startswith("https://")):
                    data["avatar_url"] = f"{protocol}://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET}/{v}"
        return data


class ArticleListResponse(BaseModel):
    """
    Thông tin rút gọn của một bài viết phục vụ cho màn hình danh sách.
    """
    id: uuid.UUID
    title: str
    slug: str
    excerpt: Optional[str] = None
    thumbnail_object_key: Optional[str] = None
    category: Optional[ArticleCategoryListResponse] = None
    tags: list[ArticleTagListResponse] = []
    author: Optional[ArticleAuthorListResponse] = None
    status: ArticleStatus
    is_featured: bool
    is_pinned: bool
    is_draft: bool
    view_count: int
    created_at: datetime
    publish_at: Optional[datetime] = None
    published_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("status", mode="before")
    @classmethod
    def map_draft_status_to_published(cls, v: Any) -> Any:
        if v == ArticleStatus.DRAFT or v == "DRAFT":
            return ArticleStatus.PUBLISHED
        return v

    @field_validator("thumbnail_object_key")
    @classmethod
    def transform_thumbnail_url(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return v
        if v.startswith("http://") or v.startswith("https://"):
            return v
        from app.core.config import settings
        protocol = "https" if settings.MINIO_SECURE else "http"
        return f"{protocol}://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET}/{v}"


class ArticlePaginationResponse(BaseModel):
    """
    Response bọc kết quả phân trang danh sách bài viết.
    """
    items: list[ArticleListResponse]
    page: int = Field(..., description="Trang hiện tại (1-based)")
    page_size: int = Field(..., description="Số lượng bài viết trên mỗi trang")
    total_items: int = Field(..., description="Tổng số bài viết thỏa mãn bộ lọc")
    total_pages: int = Field(..., description="Tổng số trang kết quả")
    has_next: bool = Field(..., description="Có trang kế tiếp hay không")
    has_previous: bool = Field(..., description="Có trang trước đó hay không")


class BulkActionEnum(str, Enum):
    """
    Các loại hành động thao tác trạng thái hàng loạt.
    """
    ARCHIVE = "archive"
    PUBLISH = "publish"
    DELETE = "delete"
    RESTORE = "restore"


class BulkStatusUpdateRequest(BaseModel):
    """
    Yêu cầu thay đổi trạng thái hàng loạt.
    """
    article_ids: list[uuid.UUID] = Field(..., min_items=1, description="Danh sách ID bài viết cần xử lý")
    action: BulkActionEnum


class BulkActionResponse(BaseModel):
    """
    Kết quả phản hồi của thao tác hàng loạt.
    """
    success_count: int = Field(..., description="Số lượng bài viết cập nhật thành công")
    failed_count: int = Field(..., description="Số lượng bài viết cập nhật thất bại")
    failed_ids: list[uuid.UUID] = Field(default=[], description="Danh sách ID bài viết bị lỗi")
    message: str = Field(..., description="Thông điệp phản hồi chi tiết")


class ArticleStatsResponse(BaseModel):
    """
    Phản hồi số liệu thống kê nhanh về bài viết.
    """
    published_count: int = Field(..., description="Số bài viết đang công khai")
    scheduled_count: int = Field(..., description="Số bài viết đã lên lịch")
    draft_count: int = Field(..., description="Số bài viết nháp")
    archived_count: int = Field(..., description="Số bài viết đã lưu trữ")
    trash_count: int = Field(..., description="Số bài viết đã bị xóa tạm trong thùng rác")
    total_views_this_month: int = Field(..., description="Tổng số lượt xem của tất cả các bài viết trong tháng hiện tại")


class ArticleAttributesUpdateRequest(BaseModel):
    """
    Yêu cầu cập nhật thuộc tính đặc biệt nhanh của bài viết.
    """
    is_featured: Optional[bool] = Field(default=None, description="Trạng thái nổi bật")
    is_pinned: Optional[bool] = Field(default=None, description="Trạng thái ghim lên đầu")


class ArticleCreateRequest(BaseModel):
    """
    Yêu cầu tạo bài viết mới.
    """
    title: str = Field(..., max_length=255, description="Tiêu đề bài viết")
    slug: Optional[str] = Field(default=None, max_length=255, description="Đường dẫn thân thiện")
    excerpt: Optional[str] = Field(default=None, description="Tóm tắt bài viết")
    content: Optional[str] = Field(default="", description="Nội dung HTML chi tiết")
    category_id: Optional[uuid.UUID] = Field(default=None, description="ID danh mục của bài viết")
    tag_ids: list[uuid.UUID] = Field(default=[], description="Danh sách ID thẻ tag liên kết")
    status: ArticleStatus = Field(default=ArticleStatus.DRAFT, description="Trạng thái bài viết")
    publish_at: Optional[datetime] = Field(default=None, description="Thời điểm hẹn giờ xuất bản")
    expire_at: Optional[datetime] = Field(default=None, description="Thời điểm hết hạn hiển thị")
    thumbnail_object_key: Optional[str] = Field(default=None, description="Key ảnh thumbnail trên MinIO")
    cover_object_key: Optional[str] = Field(default=None, description="Key ảnh bìa trên MinIO")
    is_featured: bool = Field(default=False, description="Đánh dấu nổi bật")
    is_pinned: bool = Field(default=False, description="Đánh dấu ghim lên đầu")
    is_draft: bool = Field(default=True, description="Đánh dấu bài viết nháp (chưa xuất bản chính thức)")
    
    # Hỗ trợ Front-end gửi nguyên object của GET response ngược lên
    category: Optional[Any] = Field(default=None, description="Object danh mục chứa id")
    tags: Optional[list[Any]] = Field(default=None, description="List tag objects chứa id")

    # SEO Cấu hình
    seo_title: Optional[str] = Field(default=None, max_length=255)
    seo_description: Optional[str] = Field(default=None)
    canonical_url: Optional[str] = Field(default=None)
    robots: Optional[str] = Field(default="index, follow")
    og_title: Optional[str] = Field(default=None)
    og_description: Optional[str] = Field(default=None)
    og_image: Optional[str] = Field(default=None)

    @model_validator(mode="before")
    @classmethod
    def clean_empty_strings(cls, data: Any) -> Any:
        if isinstance(data, dict):
            cleaned = {}
            for k, v in data.items():
                if v == "":
                    cleaned[k] = None
                else:
                    cleaned[k] = v
            return cleaned
        return data

    @field_validator("thumbnail_object_key", "cover_object_key", "og_image", mode="before")
    @classmethod
    def extract_raw_key(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return v
        if not isinstance(v, str):
            return v
        from app.core.config import settings
        base_prefix = f"/{settings.MINIO_BUCKET}/"
        if base_prefix in v:
            return v.split(base_prefix, 1)[1]
        prefix_host = f"{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET}/"
        if prefix_host in v:
            return v.split(prefix_host, 1)[1]
        return v


class SlugCheckResponse(BaseModel):
    """
    Kết quả phản hồi khi kiểm tra tính khả dụng của slug.
    """
    available: bool = Field(..., description="Trạng thái khả dụng của slug (True = Chưa trùng, dùng được)")
    suggested_slug: str = Field(..., description="Slug gợi ý sử dụng (đã tự động tăng hậu tố nếu bị trùng)")


class ArticleDetailResponse(ArticleListResponse):
    """
    Thông tin chi tiết đầy đủ của một bài viết phục vụ cho Form biên tập/sửa bài viết.
    """
    content: Optional[str] = ""
    cover_object_key: Optional[str] = None
    expire_at: Optional[datetime] = None
    
    # SEO fields
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    canonical_url: Optional[str] = None
    robots: Optional[str] = "index, follow"
    og_title: Optional[str] = None
    og_description: Optional[str] = None
    og_image: Optional[str] = None

    @field_validator("cover_object_key")
    @classmethod
    def transform_cover_url(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return v
        if v.startswith("http://") or v.startswith("https://"):
            return v
        from app.core.config import settings
        protocol = "https" if settings.MINIO_SECURE else "http"
        return f"{protocol}://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET}/{v}"

    @field_validator("og_image")
    @classmethod
    def transform_og_image_url(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return v
        if v.startswith("http://") or v.startswith("https://"):
            return v
        from app.core.config import settings
        protocol = "https" if settings.MINIO_SECURE else "http"
        return f"{protocol}://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET}/{v}"


class ArticleDraftsCountResponse(BaseModel):
    """
    Phản hồi số lượng bài viết nháp của tác giả hiện tại.
    """
    count: int = Field(..., description="Số lượng bài viết nháp của tác giả hiện tại")


class ArticleUpdateRequest(BaseModel):
    """
    Yêu cầu cập nhật bài viết.
    """
    title: Optional[str] = Field(default=None, max_length=255, description="Tiêu đề bài viết")
    slug: Optional[str] = Field(default=None, max_length=255, description="Đường dẫn thân thiện")
    excerpt: Optional[str] = Field(default=None, description="Tóm tắt bài viết")
    content: Optional[str] = Field(default=None, description="Nội dung HTML chi tiết")
    category_id: Optional[uuid.UUID] = Field(default=None, description="ID danh mục của bài viết")
    tag_ids: Optional[list[uuid.UUID]] = Field(default=None, description="Danh sách ID thẻ tag liên kết")
    status: Optional[ArticleStatus] = Field(default=None, description="Trạng thái bài viết")
    publish_at: Optional[datetime] = Field(default=None, description="Thời điểm hẹn giờ xuất bản")
    expire_at: Optional[datetime] = Field(default=None, description="Thời điểm hết hạn hiển thị")
    thumbnail_object_key: Optional[str] = Field(default=None, description="Key ảnh thumbnail trên MinIO")
    cover_object_key: Optional[str] = Field(default=None, description="Key ảnh bìa trên MinIO")
    is_featured: Optional[bool] = Field(default=None, description="Đánh dấu nổi bật")
    is_pinned: Optional[bool] = Field(default=None, description="Đánh dấu ghim lên đầu")
    is_draft: Optional[bool] = Field(default=None, description="Đánh dấu bài viết nháp (chưa xuất bản chính thức)")
    
    # Hỗ trợ Front-end gửi nguyên object của GET response ngược lên
    category: Optional[Any] = Field(default=None, description="Object danh mục chứa id")
    tags: Optional[list[Any]] = Field(default=None, description="List tag objects chứa id")

    # SEO Cấu hình
    seo_title: Optional[str] = Field(default=None, max_length=255)
    seo_description: Optional[str] = Field(default=None)
    canonical_url: Optional[str] = Field(default=None)
    robots: Optional[str] = Field(default=None)
    og_title: Optional[str] = Field(default=None)
    og_description: Optional[str] = Field(default=None)
    og_image: Optional[str] = Field(default=None)

    @model_validator(mode="before")
    @classmethod
    def clean_empty_strings(cls, data: Any) -> Any:
        if isinstance(data, dict):
            cleaned = {}
            for k, v in data.items():
                if v == "":
                    cleaned[k] = None
                else:
                    cleaned[k] = v
            return cleaned
        return data

    @field_validator("thumbnail_object_key", "cover_object_key", "og_image", mode="before")
    @classmethod
    def extract_raw_key(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return v
        if not isinstance(v, str):
            return v
        from app.core.config import settings
        base_prefix = f"/{settings.MINIO_BUCKET}/"
        if base_prefix in v:
            return v.split(base_prefix, 1)[1]
        prefix_host = f"{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET}/"
        if prefix_host in v:
            return v.split(prefix_host, 1)[1]
        return v


class PortalArticleResponse(ArticleListResponse):
    """
    Thông tin bài viết phục vụ cho Portal FE Client, bao gồm đầy đủ dữ liệu SEO & OpenGraph.
    """
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    canonical_url: Optional[str] = None
    robots: Optional[str] = None
    og_title: Optional[str] = None
    og_description: Optional[str] = None
    og_image: Optional[str] = None
    og_image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_og_image_url(cls, data: Any) -> Any:
        from app.core.config import settings
        protocol = "https" if settings.MINIO_SECURE else "http"
        
        # 1. Trường hợp data là đối tượng SQLAlchemy Article
        if hasattr(data, "og_image") and data.og_image:
            v = data.og_image
            if v.startswith("http://") or v.startswith("https://"):
                data.og_image_url = v
            else:
                data.og_image_url = f"{protocol}://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET}/{v}"
        
        # 2. Trường hợp data là dict (ví dụ FE gửi/test)
        elif isinstance(data, dict):
            v = data.get("og_image")
            if v:
                if v.startswith("http://") or v.startswith("https://"):
                    data["og_image_url"] = v
                else:
                    data["og_image_url"] = f"{protocol}://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET}/{v}"
        return data


class PortalArticlePaginationResponse(BaseModel):
    """
    Response bọc kết quả phân trang danh sách bài viết dành cho Portal.
    """
    items: list[PortalArticleResponse]
    page: int = Field(..., description="Trang hiện tại (1-based)")
    page_size: int = Field(..., description="Số lượng bài viết trên mỗi trang")
    total_items: int = Field(..., description="Tổng số bài viết thỏa mãn bộ lọc")
    total_pages: int = Field(..., description="Tổng số trang kết quả")
    has_next: bool = Field(..., description="Có trang kế tiếp hay không")
    has_previous: bool = Field(..., description="Có trang trước đó hay không")

    model_config = ConfigDict(from_attributes=True)


class PortalArticleDetailResponse(PortalArticleResponse):
    """
    Thông tin chi tiết bài viết phục vụ cho Portal FE Client.
    Bao gồm nội dung chi tiết, thống kê số từ/thời gian đọc và dữ liệu JSON-LD Schema.org NewsArticle tối ưu SEO.
    """
    content: str
    word_count: int
    reading_time: int
    thumbnail_url: Optional[str] = None
    cover_url: Optional[str] = None
    updated_at: Optional[datetime] = None
    json_ld: dict = Field(default={}, description="Dữ liệu cấu trúc Schema.org dạng JSON-LD cho công cụ tìm kiếm")

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_seo_and_json_ld(cls, data: Any) -> Any:
        from app.core.config import settings
        import re
        protocol = "https" if settings.MINIO_SECURE else "http"
        minio_endpoint = settings.MINIO_ENDPOINT
        minio_bucket = settings.MINIO_BUCKET

        def get_val(obj, key, default=None):
            if hasattr(obj, key):
                return getattr(obj, key)
            elif isinstance(obj, dict):
                return obj.get(key, default)
            return default

        title = get_val(data, "title")
        slug = get_val(data, "slug")
        excerpt = get_val(data, "excerpt")
        content = get_val(data, "content", "")
        
        # Resolve URLs tuyệt đối cho ảnh
        thumb_key = get_val(data, "thumbnail_object_key")
        cover_key = get_val(data, "cover_object_key")
        og_img_key = get_val(data, "og_image")

        thumb_url = None
        if thumb_key:
            thumb_url = thumb_key if (thumb_key.startswith("http://") or thumb_key.startswith("https://")) else f"{protocol}://{minio_endpoint}/{minio_bucket}/{thumb_key}"
        
        cover_url = None
        if cover_key:
            cover_url = cover_key if (cover_key.startswith("http://") or cover_key.startswith("https://")) else f"{protocol}://{minio_endpoint}/{minio_bucket}/{cover_key}"

        og_image_url = None
        if og_img_key:
            og_image_url = og_img_key if (og_img_key.startswith("http://") or og_img_key.startswith("https://")) else f"{protocol}://{minio_endpoint}/{minio_bucket}/{og_img_key}"
        elif thumb_url:
            og_image_url = thumb_url
        elif cover_url:
            og_image_url = cover_url

        # Gán ngược lại cho data
        if hasattr(data, "thumbnail_url"):
            data.thumbnail_url = thumb_url
            data.cover_url = cover_url
            data.og_image_url = og_image_url
        elif isinstance(data, dict):
            data["thumbnail_url"] = thumb_url
            data["cover_url"] = cover_url
            data["og_image_url"] = og_image_url

        # Xử lý fallbacks cho SEO
        seo_title = get_val(data, "seo_title") or title
        
        # Loại bỏ các thẻ HTML để lấy văn bản thuần cho meta description
        clean_text = re.sub(r'<[^>]+>', ' ', content)
        clean_text = " ".join(clean_text.split())
        fallback_desc = excerpt or (clean_text[:160] + "..." if len(clean_text) > 160 else clean_text)
        
        seo_desc = get_val(data, "seo_description") or fallback_desc
        robots = get_val(data, "robots") or "index, follow"
        
        canonical_url = get_val(data, "canonical_url")
        if not canonical_url and slug:
            fe_url = "http://localhost:3000"
            canonical_url = f"{fe_url}/articles/{slug}"

        og_title = get_val(data, "og_title") or seo_title
        og_desc = get_val(data, "og_description") or seo_desc

        if hasattr(data, "seo_title"):
            data.seo_title = seo_title
            data.seo_description = seo_desc
            data.robots = robots
            data.canonical_url = canonical_url
            data.og_title = og_title
            data.og_description = og_desc
        elif isinstance(data, dict):
            data["seo_title"] = seo_title
            data["seo_description"] = seo_desc
            data["robots"] = robots
            data["canonical_url"] = canonical_url
            data["og_title"] = og_title
            data["og_description"] = og_desc

        # Sinh JSON-LD Structured Data (Schema.org NewsArticle)
        publish_at = get_val(data, "publish_at") or get_val(data, "created_at")
        updated_at = get_val(data, "updated_at") or get_val(data, "created_at")
        
        author_name = "Viện Kỹ thuật và Công nghệ"
        author_obj = get_val(data, "author")
        if author_obj:
            if hasattr(author_obj, "full_name"):
                author_name = author_obj.full_name
            elif isinstance(author_obj, dict):
                author_name = author_obj.get("full_name", author_name)

        pub_iso = publish_at.isoformat() if hasattr(publish_at, "isoformat") else str(publish_at)
        upd_iso = updated_at.isoformat() if hasattr(updated_at, "isoformat") else str(updated_at)

        json_ld_data = {
            "@context": "https://schema.org",
            "@type": "NewsArticle",
            "headline": title,
            "image": [img for img in [og_image_url, thumb_url, cover_url] if img],
            "datePublished": pub_iso,
            "dateModified": upd_iso,
            "author": {
                "@type": "Person",
                "name": author_name
            },
            "publisher": {
                "@type": "Organization",
                "name": "Viện Kỹ thuật và Công nghệ - Đại học Vinh",
                "logo": {
                  "@type": "ImageObject",
                  "url": "https://viengktc.example.com/logo.png"
                }
            },
            "description": seo_desc
        }

        if hasattr(data, "json_ld"):
            data.json_ld = json_ld_data
        elif isinstance(data, dict):
            data["json_ld"] = json_ld_data

        return data




