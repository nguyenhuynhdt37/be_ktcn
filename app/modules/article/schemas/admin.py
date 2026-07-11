from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator
from app.modules.article.models import ArticleStatus
from app.modules.article.schemas.common import (
    build_article_resolved_before_validation,
    ArticleCategoryListResponse,
    ArticleTagListResponse,
    ArticleAuthorListResponse
)


class TranslationItemResponse(BaseModel):
    title: str
    slug: str
    excerpt: Optional[str] = None
    content: str
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    canonical_url: Optional[str] = None
    robots: Optional[str] = "index, follow"
    og_title: Optional[str] = None
    og_description: Optional[str] = None
    og_image: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ArticleCreateRequest(BaseModel):
    category_id: Optional[uuid.UUID] = Field(default=None)
    department_id: Optional[uuid.UUID] = Field(default=None)
    program_id: Optional[uuid.UUID] = Field(default=None)
    article_type: str = Field(default="news", max_length=30)
    tag_ids: list[uuid.UUID] = Field(default=[])
    status: ArticleStatus = Field(default=ArticleStatus.DRAFT)
    publish_at: Optional[datetime] = Field(default=None)
    expire_at: Optional[datetime] = Field(default=None)
    thumbnail_object_key: Optional[str] = Field(default=None)
    cover_object_key: Optional[str] = Field(default=None)
    is_pinned: bool = Field(default=False)
    is_draft: bool = Field(default=True)
    category: Optional[Any] = None
    tags: Optional[list[Any]] = None
    translations: dict[str, Optional[TranslationItemResponse]] = Field(...)

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

    @field_validator("thumbnail_object_key", "cover_object_key", mode="before")
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


class ArticleUpdateRequest(BaseModel):
    category_id: Optional[uuid.UUID] = None
    department_id: Optional[uuid.UUID] = None
    program_id: Optional[uuid.UUID] = None
    article_type: Optional[str] = Field(default=None, max_length=30)
    tag_ids: Optional[list[uuid.UUID]] = None
    status: Optional[ArticleStatus] = None
    publish_at: Optional[datetime] = None
    expire_at: Optional[datetime] = None
    thumbnail_object_key: Optional[str] = None
    cover_object_key: Optional[str] = None
    is_pinned: Optional[bool] = None
    is_draft: Optional[bool] = None
    category: Optional[Any] = None
    tags: Optional[list[Any]] = None
    translations: Optional[dict[str, Optional[TranslationItemResponse]]] = None

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

    @field_validator("thumbnail_object_key", "cover_object_key", mode="before")
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


class AdminArticleResponse(BaseModel):
    id: uuid.UUID
    category_id: Optional[uuid.UUID] = None
    department_id: Optional[uuid.UUID] = None
    program_id: Optional[uuid.UUID] = None
    article_type: str = "news"
    author_id: Optional[uuid.UUID] = None
    status: ArticleStatus
    is_draft: bool
    is_pinned: bool
    sort_order: int
    view_count: int
    word_count: int
    reading_time: int
    created_at: datetime
    publish_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    expire_at: Optional[datetime] = None
    thumbnail_object_key: Optional[str] = None
    cover_object_key: Optional[str] = None
    category: Optional[ArticleCategoryListResponse] = None
    author: Optional[ArticleAuthorListResponse] = None
    tags: list[ArticleTagListResponse] = []
    is_translated: dict[str, bool] = {}
    translations: dict[str, Any] = {}

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_article_before_validation(cls, data: Any) -> Any:
        return build_article_resolved_before_validation(data)


class ArticleSEOAnalyzeRequest(BaseModel):
    title: Optional[str] = Field(default=None, description="Tiêu đề bài viết hiện tại trên form")
    content: Optional[str] = Field(default=None, description="Nội dung bài viết hiện tại trên form (HTML)")
    excerpt: Optional[str] = Field(default=None, description="Tóm tắt bài viết hiện tại trên form")
    seo_title: Optional[str] = Field(default=None, description="Tiêu đề SEO hiện tại trên form")
    seo_description: Optional[str] = Field(default=None, description="Mô tả SEO hiện tại trên form")
    focus_keyword: Optional[str] = Field(default=None, description="Từ khóa chính người dùng nhập để phân tích")
    thumbnail_object_key: Optional[str] = Field(default=None, description="Ảnh đại diện hiện tại trên form (chưa lưu)")
    slug: Optional[str] = Field(default=None, description="Slug hiện tại trên form (chưa lưu)")
    lang: str = Field(default="vi", description="Ngôn ngữ phân tích (mặc định: vi)")


class SEOElementIssue(BaseModel):
    type: str = Field(..., description="Loại vấn đề, ví dụ: 'title_length', 'missing_alt'")
    message: str = Field(..., description="Thông điệp cảnh báo / đề xuất sửa lỗi")


class SEOElementAnalysis(BaseModel):
    score: int = Field(..., ge=0, le=100, description="Điểm số cho yếu tố này (0-100)")
    status: str = Field(..., description="Trạng thái đánh giá: 'good', 'warning', 'error'")
    message: str = Field(..., description="Nhận xét tổng quan")
    issues: list[SEOElementIssue] = Field(default=[], description="Các vấn đề chi tiết cần khắc phục")


class SEOAuditDetails(BaseModel):
    title_analysis: SEOElementAnalysis = Field(..., description="Phân tích tiêu đề")
    meta_description_analysis: SEOElementAnalysis = Field(..., description="Phân tích mô tả SEO / tóm tắt")
    content_analysis: SEOElementAnalysis = Field(..., description="Phân tích nội dung chính")
    link_analysis: SEOElementAnalysis = Field(..., description="Phân tích các liên kết")


class InternalLinkSuggestion(BaseModel):
    anchor_text: str = Field(..., description="Cụm từ trong bài viết có thể gắn link")
    url: str = Field(..., description="URL đề xuất liên kết đến")
    reason: str = Field(..., description="Lý do đề xuất liên kết này")


class GooglePreviewInfo(BaseModel):
    title: str = Field(..., description="Tiêu đề hiển thị trên Google")
    url: str = Field(..., description="URL hiển thị trên Google")
    description: str = Field(..., description="Mô tả hiển thị trên Google")


class ArticleSEOAnalyzeResponse(BaseModel):
    score: int = Field(..., ge=0, le=100, description="Điểm SEO tổng quan tính bằng Rule Engine (0-100)")
    status: str = Field(..., description="Trạng thái SEO tổng thể: 'good', 'warning', 'error'")
    issues: list[SEOElementIssue] = Field(default=[], description="Danh sách gộp tất cả các vấn đề cần khắc phục từ Rule Engine")
    suggestions: list[str] = Field(default=[], description="Các gợi ý cải thiện tổng quan và văn phong từ AI")
    generated_seo_title: str = Field(default="", description="Tiêu đề SEO gợi ý tối ưu từ AI")
    generated_meta_description: str = Field(default="", description="Mô tả SEO gợi ý tối ưu từ AI")
    focus_keywords: list[str] = Field(default=[], description="Gợi ý các từ khóa phụ liên quan từ AI")
    internal_links: list[InternalLinkSuggestion] = Field(default=[], description="Gợi ý chèn internal link")
    google_preview: GooglePreviewInfo = Field(..., description="Thông tin preview kết quả tìm kiếm Google")


class ArticleSEORewriteRequest(BaseModel):
    content: str = Field(..., description="Nội dung bài viết dạng HTML cần viết lại")
    focus_keyword: Optional[str] = Field(default=None, description="Từ khóa chính cần tối ưu hóa khi viết lại")
    tone: Optional[str] = Field(default="chuyên nghiệp", description="Văn phong viết lại: chuyên nghiệp, thân thiện, sáng tạo, học thuật")
    lang: str = Field(default="vi", description="Ngôn ngữ viết bài (mặc định: vi)")


class ArticleSEORewriteResponse(BaseModel):
    content: str = Field(..., description="Nội dung bài viết mới dạng HTML đã được tối ưu hóa và khôi phục hình ảnh")


class ArticleGenerateByIdeaRequest(BaseModel):
    idea: str = Field(..., description="Mô tả ý tưởng, dàn ý hoặc chủ đề bài viết")
    focus_keyword: Optional[str] = Field(default=None, description="Từ khóa chính mong muốn")
    tone: Optional[str] = Field(default="chuyên nghiệp", description="Văn phong bài viết")
    lang: str = Field(default="vi", description="Ngôn ngữ (mặc định: vi)")


class ArticleGenerateByIdeaResponse(BaseModel):
    title: str = Field(..., description="Tiêu đề bài viết gợi ý")
    excerpt: str = Field(..., description="Tóm tắt bài viết gợi ý")
    content: str = Field(..., description="Nội dung bài viết hoàn chỉnh dạng HTML chuẩn SEO")
    seo_title: str = Field(..., description="Tiêu đề SEO gợi ý")
    seo_description: str = Field(..., description="Mô tả SEO gợi ý")
    slug: str = Field(..., description="Slug gợi ý chuẩn hóa")


class ArticleSummaryRequest(BaseModel):
    content: str = Field(..., description="Nội dung bài viết dạng HTML cần tóm tắt")
    max_length: Optional[int] = Field(default=100, description="Độ dài tối đa tính bằng số từ (words) của tóm tắt gợi ý. Mặc định: 100 từ")
    lang: str = Field(default="vi", description="Ngôn ngữ viết bài (mặc định: vi)")


class ArticleSummaryResponse(BaseModel):
    summary: str = Field(..., description="Nội dung tóm tắt bài viết dạng text ngắn gọn (văn bản thuần)")



