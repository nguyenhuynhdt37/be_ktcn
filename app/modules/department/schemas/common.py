import uuid
from typing import Literal, Optional, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator


def safe_getattr(obj: Any, attr: str, default: Any = None) -> Any:
    """Helper truy xuất an toàn thuộc tính của object SQLAlchemy tránh MissingGreenlet."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(attr, default)
    # Thử lấy từ __dict__ trước để tránh kích hoạt lazy-loading
    if hasattr(obj, "__dict__") and attr in obj.__dict__:
        return obj.__dict__[attr]
    return getattr(obj, attr, default)


def build_department_resolved(data: Any) -> dict:
    """
    Helper chuyển đổi object Department db sang dictionary phẳng
    chứa cả translations và is_translated an toàn cho cả Pydantic validator.
    """
    from app.core.config import settings
    protocol = "https" if settings.MINIO_SECURE else "http"

    def transform_url(v: Optional[str]) -> Optional[str]:
        if not v:
            return v
        if v.startswith("http://") or v.startswith("https://") or v.startswith("data:"):
            return v
        return f"{protocol}://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET}/{v}"

    if isinstance(data, dict):
        translations = data.get("translations") or {}
        is_translated = data.get("is_translated") or {}
        for code in ["vi", "en"]:
            if code not in translations:
                translations[code] = {}
            if code not in is_translated:
                translations[code]["is_translated"] = bool(translations[code].get("name"))
        data["translations"] = translations
        data["is_translated"] = is_translated
        
        # Transform thumbnail URL
        if "thumbnail_object_key" in data:
            data["thumbnail_object_key"] = transform_url(data["thumbnail_object_key"])
        if "banner_object_key" in data:
            data["banner_object_key"] = transform_url(data["banner_object_key"])
        return data

    translations_dict = {
        "vi": {"name": "", "description": "", "short_description": "", "mission": "", "vision": "", "seo_title": "", "seo_description": "", "slug": "", "is_translated": False},
        "en": {"name": "", "description": "", "short_description": "", "mission": "", "vision": "", "seo_title": "", "seo_description": "", "slug": "", "is_translated": False}
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
                    "description": trans.description,
                    "short_description": trans.short_description,
                    "mission": trans.mission,
                    "vision": trans.vision,
                    "seo_title": trans.seo_title,
                    "seo_description": trans.seo_description,
                    "slug": trans.slug,
                    "is_translated": True
                }
                is_translated[lang_code] = True

    db_dict = {
        "id": safe_getattr(data, "id", None),
        "code": safe_getattr(data, "code", None),
        "unit_type": safe_getattr(data, "unit_type", "department"),
        "parent_id": safe_getattr(data, "parent_id", None),
        "thumbnail_object_key": transform_url(safe_getattr(data, "thumbnail_object_key", None)),
        "banner_object_key": transform_url(safe_getattr(data, "banner_object_key", None)),
        "phone": safe_getattr(data, "phone", None),
        "email": safe_getattr(data, "email", None),
        "website": safe_getattr(data, "website", None),
        "office": safe_getattr(data, "office", None),
        "sort_order": safe_getattr(data, "sort_order", 0),
        "is_active": safe_getattr(data, "is_active", True),
        "content_status": safe_getattr(data, "content_status", "draft"),
        "is_translated": is_translated,
        "translations": translations_dict,
        "name": safe_getattr(data, "name", ""),
        "description": safe_getattr(data, "description", None),
        "short_description": safe_getattr(data, "short_description", None),
        "mission": safe_getattr(data, "mission", None),
        "vision": safe_getattr(data, "vision", None),
        "seo_title": safe_getattr(data, "seo_title", None),
        "seo_description": safe_getattr(data, "seo_description", None),
        "slug": safe_getattr(data, "slug", ""),
        "staff_count": safe_getattr(data, "staff_count", 0),
        "created_at": safe_getattr(data, "created_at", None),
        "updated_at": safe_getattr(data, "updated_at", None)
    }
    return db_dict


class TranslationItemResponse(BaseModel):
    """Schema cho từng bản dịch của Department."""
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    short_description: Optional[str] = None
    mission: Optional[str] = None
    vision: Optional[str] = None
    seo_title: Optional[str] = Field(None, max_length=255)
    seo_description: Optional[str] = None
    slug: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DepartmentCreate(BaseModel):
    """Payload tạo mới bộ môn."""
    code: Optional[str] = Field(None, max_length=50)
    unit_type: Literal["school", "faculty", "department", "office", "center", "lab"] = "department"
    parent_id: Optional[uuid.UUID] = None
    thumbnail_object_key: Optional[str] = None
    banner_object_key: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    office: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True
    content_status: Literal["draft", "review", "published"] = "draft"
    translations: dict[str, TranslationItemResponse] = Field(..., description="Bản dịch bộ môn")

    @field_validator("phone", "email", "website", "office", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: Any) -> Any:
        if v == "":
            return None
        return v


class DepartmentUpdate(BaseModel):
    """Payload cập nhật bộ môn."""
    code: Optional[str] = Field(None, max_length=50)
    unit_type: Optional[Literal["school", "faculty", "department", "office", "center", "lab"]] = None
    parent_id: Optional[uuid.UUID] = None
    thumbnail_object_key: Optional[str] = None
    banner_object_key: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    office: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    content_status: Optional[Literal["draft", "review", "published"]] = None
    translations: Optional[dict[str, TranslationItemResponse]] = None

    @field_validator("phone", "email", "website", "office", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: Any) -> Any:
        if v == "":
            return None
        return v
