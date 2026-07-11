import uuid
from datetime import date
from typing import Literal
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator


def safe_getattr(obj: Any, attr: str, default: Any = None) -> Any:
    """Helper truy xuất an toàn thuộc tính của object SQLAlchemy tránh MissingGreenlet."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(attr, default)
    if hasattr(obj, "__dict__") and attr in obj.__dict__:
        return obj.__dict__[attr]
    return getattr(obj, attr, default)


def build_staff_resolved(data: Any) -> dict:
    """
    Helper chuyển đổi object Staff db sang dictionary phẳng
    chứa cả translations và is_translated an toàn.
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
                translations[code]["is_translated"] = bool(
                    translations[code].get("biography") or translations[code].get("research_interests")
                )
        data["translations"] = translations
        data["is_translated"] = is_translated
        if "avatar_object_key" in data:
            data["avatar_object_key"] = transform_url(data["avatar_object_key"])
        return data

    translations_dict = {
        "vi": {"biography": None, "research_interests": None, "is_translated": False},
        "en": {"biography": None, "research_interests": None, "is_translated": False}
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
                    "biography": trans.biography,
                    "research_interests": trans.research_interests,
                    "is_translated": True
                }
                is_translated[lang_code] = True

    db_dict = {
        "id": safe_getattr(data, "id", None),
        "department_id": safe_getattr(data, "department_id", None),
        "position_id": safe_getattr(data, "position_id", None),
        "academic_title_id": safe_getattr(data, "academic_title_id", None),
        "degree_id": safe_getattr(data, "degree_id", None),
        "full_name": safe_getattr(data, "full_name", ""),
        "normalized_full_name": safe_getattr(data, "normalized_full_name", None),
        "english_name": safe_getattr(data, "english_name", None),
        "date_of_birth": safe_getattr(data, "date_of_birth", None),
        "gender": safe_getattr(data, "gender", None),
        "slug": safe_getattr(data, "slug", ""),
        "avatar_object_key": transform_url(safe_getattr(data, "avatar_object_key", None)),
        "email": safe_getattr(data, "email", None),
        "phone": safe_getattr(data, "phone", None),
        "website": safe_getattr(data, "website", None),
        "office": safe_getattr(data, "office", None),
        "sort_order": safe_getattr(data, "sort_order", 0),
        "is_active": safe_getattr(data, "is_active", True),
        "profile_status": safe_getattr(data, "profile_status", "imported"),
        "is_visible": safe_getattr(data, "is_visible", False),
        "note": safe_getattr(data, "note", None),
        "source_type": safe_getattr(data, "source_type", None),
        "source_note": safe_getattr(data, "source_note", None),
        "source_file_id": safe_getattr(data, "source_file_id", None),
        "is_translated": is_translated,
        "translations": translations_dict,
        "academic_title": safe_getattr(data, "academic_title_resolved", None),
        "degree": safe_getattr(data, "degree_resolved", None),
        "biography": safe_getattr(data, "biography", None),
        "research_interests": safe_getattr(data, "research_interests", None),
        "department": safe_getattr(data, "department", None),
        "position": safe_getattr(data, "position", None),
        "created_at": safe_getattr(data, "created_at", None),
        "updated_at": safe_getattr(data, "updated_at", None)
    }
    return db_dict


class TranslationItemResponse(BaseModel):
    """Schema cho từng bản dịch của Staff."""
    biography: Optional[str] = None
    research_interests: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class StaffCreate(BaseModel):
    """Payload tạo giảng viên mới."""
    department_id: uuid.UUID
    position_id: uuid.UUID
    academic_title_id: Optional[uuid.UUID] = None
    degree_id: Optional[uuid.UUID] = None
    full_name: str = Field(..., max_length=255)
    english_name: Optional[str] = Field(None, max_length=255)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=20)
    avatar_object_key: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    office: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True
    profile_status: Literal["imported", "pending_review", "completed", "published"] = "pending_review"
    is_visible: bool = True
    note: Optional[str] = None
    source_type: Optional[str] = Field(None, max_length=50)
    source_note: Optional[str] = None
    source_file_id: Optional[uuid.UUID] = None
    translations: dict[str, TranslationItemResponse] = Field(..., description="Bản dịch thông tin giảng viên")

    @field_validator("english_name", "gender", "email", "phone", "website", "office", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: Any) -> Any:
        if v == "":
            return None
        return v


class StaffUpdate(BaseModel):
    """Payload cập nhật giảng viên."""
    department_id: Optional[uuid.UUID] = None
    position_id: Optional[uuid.UUID] = None
    academic_title_id: Optional[uuid.UUID] = None
    degree_id: Optional[uuid.UUID] = None
    full_name: Optional[str] = None
    english_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    avatar_object_key: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    office: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    profile_status: Optional[Literal["imported", "pending_review", "completed", "published"]] = None
    is_visible: Optional[bool] = None
    note: Optional[str] = None
    source_type: Optional[str] = None
    source_note: Optional[str] = None
    source_file_id: Optional[uuid.UUID] = None
    translations: Optional[dict[str, TranslationItemResponse]] = None

    @field_validator("english_name", "gender", "email", "phone", "website", "office", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: Any) -> Any:
        if v == "":
            return None
        return v
