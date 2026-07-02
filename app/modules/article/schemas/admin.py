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
    tag_ids: list[uuid.UUID] = Field(default=[])
    status: ArticleStatus = Field(default=ArticleStatus.DRAFT)
    publish_at: Optional[datetime] = Field(default=None)
    expire_at: Optional[datetime] = Field(default=None)
    thumbnail_object_key: Optional[str] = Field(default=None)
    cover_object_key: Optional[str] = Field(default=None)
    is_featured: bool = Field(default=False)
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
    tag_ids: Optional[list[uuid.UUID]] = None
    status: Optional[ArticleStatus] = None
    publish_at: Optional[datetime] = None
    expire_at: Optional[datetime] = None
    thumbnail_object_key: Optional[str] = None
    cover_object_key: Optional[str] = None
    is_featured: Optional[bool] = None
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
    author_id: Optional[uuid.UUID] = None
    status: ArticleStatus
    is_draft: bool
    is_featured: bool
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
