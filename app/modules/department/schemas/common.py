import uuid
from typing import Optional, Any
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
        return data

    translations_dict = {
        "vi": {"name": "", "description": "", "slug": "", "is_translated": False},
        "en": {"name": "", "description": "", "slug": "", "is_translated": False}
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
                    "slug": trans.slug,
                    "is_translated": True
                }
                is_translated[lang_code] = True

    db_dict = {
        "id": safe_getattr(data, "id", None),
        "thumbnail_object_key": safe_getattr(data, "thumbnail_object_key", None),
        "phone": safe_getattr(data, "phone", None),
        "email": safe_getattr(data, "email", None),
        "website": safe_getattr(data, "website", None),
        "office": safe_getattr(data, "office", None),
        "sort_order": safe_getattr(data, "sort_order", 0),
        "is_active": safe_getattr(data, "is_active", True),
        "is_translated": is_translated,
        "translations": translations_dict,
        "name": safe_getattr(data, "name", ""),
        "description": safe_getattr(data, "description", None),
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
    slug: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DepartmentCreate(BaseModel):
    """Payload tạo mới bộ môn."""
    thumbnail_object_key: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    office: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True
    translations: dict[str, TranslationItemResponse] = Field(..., description="Bản dịch bộ môn")

    @field_validator("phone", "email", "website", "office", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: Any) -> Any:
        if v == "":
            return None
        return v


class DepartmentUpdate(BaseModel):
    """Payload cập nhật bộ môn."""
    thumbnail_object_key: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    office: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    translations: Optional[dict[str, TranslationItemResponse]] = None

    @field_validator("phone", "email", "website", "office", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: Any) -> Any:
        if v == "":
            return None
        return v
