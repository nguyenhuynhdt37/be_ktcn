from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator


def safe_getattr(obj: Any, attr: str, default: Any = None) -> Any:
    if not obj:
        return default
    if isinstance(obj, dict):
        return obj.get(attr, default)
    if hasattr(obj, "__dict__") and attr in obj.__dict__:
        return obj.__dict__[attr]
    if attr in ["articles", "translations"]:
        return default
    try:
        return getattr(obj, attr, default)
    except AttributeError:
        return default


def build_tag_resolved_before_validation(data: Any) -> Any:
    if not data:
        return data

    if isinstance(data, dict):
        translations = data.get("translations") or {}
        is_translated = data.get("is_translated") or {}
        for code in ["vi", "en"]:
            if code not in translations:
                translations[code] = {}
            if code not in is_translated:
                is_translated[code] = bool(translations[code].get("name"))
            translations[code]["is_translated"] = is_translated[code]
        data["translations"] = translations
        data["is_translated"] = is_translated
        if "article_count" not in data:
            data["article_count"] = 0
        return data

    translations_dict = {
        "vi": {"name": "", "slug": "", "description": "", "is_translated": False},
        "en": {"name": "", "slug": "", "description": "", "is_translated": False}
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
                    "name": trans.name,
                    "slug": trans.slug,
                    "description": trans.description,
                    "is_translated": True
                }
                is_translated[lang_code] = True

    db_dict = {
        "id": safe_getattr(data, "id", None),
        "color": safe_getattr(data, "color", None),
        "usage_count": safe_getattr(data, "usage_count", 0),
        "article_count": safe_getattr(data, "article_count", 0),
        "sort_order": safe_getattr(data, "sort_order", 0),
        "is_active": safe_getattr(data, "is_active", True),
        "created_at": safe_getattr(data, "created_at", None),
        "updated_at": safe_getattr(data, "updated_at", None),
        "is_translated": is_translated,
        "translations": translations_dict,
        
        # Flat resolved fields fallback cho Portal
        "name": safe_getattr(data, "name", ""),
        "slug": safe_getattr(data, "slug", ""),
        "description": safe_getattr(data, "description", None),
    }
    return db_dict


class TagStatusUpdate(BaseModel):
    is_active: bool = Field(..., description="Trạng thái hoạt động (True = Bật, False = Tắt)")


class TagSlugCheckResponse(BaseModel):
    """Phản hồi kiểm tra trùng lặp slug của Tag."""
    exists: bool = Field(..., description="Slug có trùng lặp trong hệ thống hay không")
    suggested_slug: str = Field(..., description="Gợi ý slug mới không bị trùng")

