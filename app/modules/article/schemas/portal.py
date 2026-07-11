from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, model_validator
from app.modules.article.models import ArticleStatus
from app.modules.article.schemas.common import (
    build_article_resolved_before_validation,
    ArticleCategoryListResponse,
    ArticleTagListResponse,
    ArticleAuthorListResponse
)


class PortalArticleListResponse(BaseModel):
    id: uuid.UUID
    category_id: Optional[uuid.UUID] = None
    department_id: Optional[uuid.UUID] = None
    program_id: Optional[uuid.UUID] = None
    article_type: str = "news"
    author_id: Optional[uuid.UUID] = None
    status: ArticleStatus
    is_pinned: bool
    view_count: int
    created_at: datetime
    publish_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    thumbnail_object_key: Optional[str] = None
    category: Optional[ArticleCategoryListResponse] = None
    author: Optional[ArticleAuthorListResponse] = None
    tags: list[ArticleTagListResponse] = []
    
    # Flat resolved fields
    title: str = ""
    slug: str = ""
    excerpt: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_article_before_validation(cls, data: Any) -> Any:
        return build_article_resolved_before_validation(data)


class PortalArticleResponse(BaseModel):
    id: uuid.UUID
    category_id: Optional[uuid.UUID] = None
    department_id: Optional[uuid.UUID] = None
    program_id: Optional[uuid.UUID] = None
    article_type: str = "news"
    author_id: Optional[uuid.UUID] = None
    status: ArticleStatus
    is_pinned: bool
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
    
    # Flat resolved fields
    title: str = ""
    slug: str = ""
    excerpt: Optional[str] = None
    content: str = ""
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    canonical_url: Optional[str] = None
    robots: Optional[str] = "index, follow"
    og_title: Optional[str] = None
    og_description: Optional[str] = None
    og_image: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_article_before_validation(cls, data: Any) -> Any:
        return build_article_resolved_before_validation(data)


class PortalArticlePaginationResponse(BaseModel):
    items: list[PortalArticleListResponse]
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool

