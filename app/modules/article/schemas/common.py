from __future__ import annotations
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator
from app.modules.article.models import ArticleStatus
from app.core.config import resolve_html_urls

def safe_getattr(obj: Any, attr: str, default: Any = None) -> Any:
    if not obj:
        return default
    if isinstance(obj, dict):
        return obj.get(attr, default)
    if hasattr(obj, "__dict__") and attr in obj.__dict__:
        return obj.__dict__[attr]
    if attr in ["category", "author", "tags", "translations"]:
        return default
    try:
        return getattr(obj, attr, default)
    except AttributeError:
        return default


def build_article_resolved_before_validation(data: Any) -> Any:
    if not data:
        return data

    if isinstance(data, dict):
        translations = data.get("translations") or {}
        is_translated = data.get("is_translated") or {}
        for code in ["vi", "en"]:
            if code not in translations:
                translations[code] = {}
            if code not in is_translated:
                is_translated[code] = bool(translations[code].get("title"))
            translations[code]["is_translated"] = is_translated[code]
        data["translations"] = translations
        data["is_translated"] = is_translated
        if "article_count" not in data:
            data["article_count"] = 0
        return data

    translations_dict = {
        "vi": {"title": "", "slug": "", "excerpt": "", "content": "", "seo_title": "", "seo_description": "", "canonical_url": "", "robots": "index, follow", "og_title": "", "og_description": "", "og_image": "", "is_translated": False},
        "en": {"title": "", "slug": "", "excerpt": "", "content": "", "seo_title": "", "seo_description": "", "canonical_url": "", "robots": "index, follow", "og_title": "", "og_description": "", "og_image": "", "is_translated": False}
    }
    is_translated = {
        "vi": False,
        "en": False
    }
    
    raw_translations = safe_getattr(data, "translations", []) or []
    if isinstance(raw_translations, list):
        for trans in raw_translations:
            lang_code = None
            if getattr(trans, "language", None):
                lang_code = trans.language.code
            if lang_code:
                translations_dict[lang_code] = {
                    "title": trans.title,
                    "slug": trans.slug,
                    "excerpt": trans.excerpt,
                    "content": resolve_html_urls(trans.content),
                    "seo_title": trans.seo_title,
                    "seo_description": trans.seo_description,
                    "canonical_url": trans.canonical_url,
                    "robots": trans.robots,
                    "og_title": trans.og_title,
                    "og_description": trans.og_description,
                    "og_image": trans.og_image,
                    "is_translated": True
                }
                is_translated[lang_code] = True

    def transform_url(v: Optional[str]) -> Optional[str]:
        if not v:
            return v
        if v.startswith("http://") or v.startswith("https://") or v.startswith("data:"):
            return v
        v_clean = v.lstrip("/")
        from app.core.config import settings
        protocol = "https" if settings.MINIO_SECURE else "http"
        return f"{protocol}://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET}/{v_clean}"

    thumbnail_key = safe_getattr(data, "thumbnail_object_key", None)
    cover_key = safe_getattr(data, "cover_object_key", None)

    # Resolve category phẳng thông minh
    category_obj = safe_getattr(data, "category", None)
    category_data = None
    if category_obj:
        cat_id = safe_getattr(category_obj, "id", None)
        cat_name = safe_getattr(category_obj, "name", "")
        cat_slug = safe_getattr(category_obj, "slug", "")
        
        if not cat_name or not cat_slug:
            cat_translations = safe_getattr(category_obj, "translations", []) or []
            vi_trans = None
            first_trans = None
            for trans in cat_translations:
                lang_code = None
                if getattr(trans, "language", None):
                    lang_code = trans.language.code
                elif isinstance(trans, dict) and "language" in trans:
                    lang_code = trans["language"].get("code")
                
                if lang_code == "vi":
                    vi_trans = trans
                    break
                if not first_trans:
                    first_trans = trans
            
            target_trans = vi_trans or first_trans
            if target_trans:
                cat_name = safe_getattr(target_trans, "name", "")
                cat_slug = safe_getattr(target_trans, "slug", "")
            else:
                cat_name = safe_getattr(category_obj, "name", "")
                cat_slug = safe_getattr(category_obj, "slug", "")
                
        category_data = {
            "id": cat_id,
            "name": cat_name,
            "slug": cat_slug
        }

    # Resolve tags phẳng thông minh
    tags_list = safe_getattr(data, "tags", []) or []
    resolved_tags = []
    for tag_obj in tags_list:
        tag_id = safe_getattr(tag_obj, "id", None)
        tag_name = safe_getattr(tag_obj, "name", "")
        tag_slug = safe_getattr(tag_obj, "slug", "")
        tag_color = safe_getattr(tag_obj, "color", None)
        
        if not tag_name or not tag_slug:
            tag_translations = safe_getattr(tag_obj, "translations", []) or []
            vi_trans = None
            first_trans = None
            for trans in tag_translations:
                lang_code = None
                if getattr(trans, "language", None):
                    lang_code = trans.language.code
                elif isinstance(trans, dict) and "language" in trans:
                    lang_code = trans["language"].get("code")
                
                if lang_code == "vi":
                    vi_trans = trans
                    break
                if not first_trans:
                    first_trans = trans
            
            target_trans = vi_trans or first_trans
            if target_trans:
                tag_name = safe_getattr(target_trans, "name", "")
                tag_slug = safe_getattr(target_trans, "slug", "")
            else:
                tag_name = safe_getattr(tag_obj, "name", "")
                tag_slug = safe_getattr(tag_obj, "slug", "")
                
        resolved_tags.append({
            "id": tag_id,
            "name": tag_name,
            "slug": tag_slug,
            "color": tag_color
        })

    db_dict = {
        "id": safe_getattr(data, "id", None),
        "category_id": safe_getattr(data, "category_id", None),
        "author_id": safe_getattr(data, "author_id", None),
        "status": safe_getattr(data, "status", ArticleStatus.DRAFT),
        "is_draft": safe_getattr(data, "is_draft", True),
        "is_pinned": safe_getattr(data, "is_pinned", False),
        "sort_order": safe_getattr(data, "sort_order", 0),
        "view_count": safe_getattr(data, "view_count", 0),
        "word_count": safe_getattr(data, "word_count", 0),
        "reading_time": safe_getattr(data, "reading_time", 0),
        "created_at": safe_getattr(data, "created_at", None),
        "publish_at": safe_getattr(data, "publish_at", None),
        "published_at": safe_getattr(data, "published_at", None),
        "expire_at": safe_getattr(data, "expire_at", None),
        "thumbnail_object_key": transform_url(thumbnail_key),
        "cover_object_key": transform_url(cover_key),
        "category": category_data,
        "author": safe_getattr(data, "author", None),
        "tags": resolved_tags,
        "is_translated": is_translated,
        "translations": translations_dict,
        
        # Flat fields fallback cho Portal
        "title": safe_getattr(data, "title", ""),
        "slug": safe_getattr(data, "slug", ""),
        "excerpt": safe_getattr(data, "excerpt", None),
        "content": resolve_html_urls(safe_getattr(data, "content", "")),
        "seo_title": safe_getattr(data, "seo_title", None),
        "seo_description": safe_getattr(data, "seo_description", None),
        "canonical_url": safe_getattr(data, "canonical_url", None),
        "robots": safe_getattr(data, "robots", "index, follow"),
        "og_title": safe_getattr(data, "og_title", None),
        "og_description": safe_getattr(data, "og_description", None),
        "og_image": transform_url(safe_getattr(data, "og_image", None)),
    }
    return db_dict


class ArticleCategoryListResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    model_config = ConfigDict(from_attributes=True)


class ArticleTagListResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    color: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class ArticleAuthorListResponse(BaseModel):
    id: uuid.UUID
    username: str
    full_name: str
    avatar_url: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_avatar_url(cls, data: Any) -> Any:
        prefix = "/api/v1/portal/media/file/"
        if hasattr(data, "avatar") and data.avatar:
            data.avatar_url = f"{prefix}{data.avatar.object_key}"
        elif hasattr(data, "avatar_url") and data.avatar_url:
            v = data.avatar_url
            if not v.startswith(prefix):
                if "files/" in v:
                    object_key = "files/" + v.split("files/")[-1]
                    data.avatar_url = f"{prefix}{object_key}"
                else:
                    data.avatar_url = f"{prefix}{v}"
        elif isinstance(data, dict):
            avatar = data.get("avatar")
            if avatar and isinstance(avatar, dict) and avatar.get("object_key"):
                data["avatar_url"] = f"{prefix}{avatar['object_key']}"
            elif data.get("avatar_url"):
                v = data["avatar_url"]
                if not v.startswith(prefix):
                    if "files/" in v:
                        object_key = "files/" + v.split("files/")[-1]
                        data["avatar_url"] = f"{prefix}{object_key}"
                    else:
                        data["avatar_url"] = f"{prefix}{v}"
        return data


class BulkActionEnum(str, Enum):
    ARCHIVE = "archive"
    PUBLISH = "publish"
    DELETE = "delete"
    RESTORE = "restore"


class BulkStatusUpdateRequest(BaseModel):
    article_ids: list[uuid.UUID] = Field(..., min_items=1)
    action: BulkActionEnum


class BulkActionResponse(BaseModel):
    success_count: int
    failed_count: int
    failed_ids: list[uuid.UUID] = []
    message: str


class ArticleStatsResponse(BaseModel):
    published_count: int
    scheduled_count: int
    draft_count: int
    archived_count: int
    trash_count: int
    total_views_this_month: int


class ArticleAttributesUpdateRequest(BaseModel):
    is_pinned: Optional[bool] = None


class SlugCheckResponse(BaseModel):
    available: bool
    suggested_slug: str


class ArticleDraftsCountResponse(BaseModel):
    count: int
