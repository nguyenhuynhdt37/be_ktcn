from __future__ import annotations
import uuid
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator


def safe_getattr(obj: Any, attr: str, default: Any = None) -> Any:
    """Truy cập thuộc tính của đối tượng một cách an toàn, tránh kích hoạt AttributeError/MissingGreenlet của SQLAlchemy mapper."""
    if not obj:
        return default
    if isinstance(obj, dict):
        return obj.get(attr, default)
    # Check trực tiếp trong __dict__ trước (nơi lưu các thuộc tính gán động ở runtime hoặc relationships đã load)
    if hasattr(obj, "__dict__") and attr in obj.__dict__:
        return obj.__dict__[attr]
    # Tránh kích hoạt lazy load cho các relationship chưa được load
    if attr in ["children", "translations"]:
        return default
    try:
        # Fallback về getattr tiêu chuẩn
        return getattr(obj, attr, default)
    except AttributeError:
        return default


def build_seo_resolved_before_validation(data: Any) -> Any:
    """Helper chuyển đổi đối tượng Category (ORM hoặc dict) để xử lý translations."""
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
        if "children" not in data:
            data["children"] = []
        return data

    translations_dict = {
        "vi": {"name": "", "slug": "", "description": "", "seo_title": "", "seo_description": "", "is_translated": False},
        "en": {"name": "", "slug": "", "description": "", "seo_title": "", "seo_description": "", "is_translated": False}
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
                    "seo_title": trans.seo_title,
                    "seo_description": trans.seo_description,
                    "is_translated": True
                }
                is_translated[lang_code] = True

    db_dict = {
        "id": safe_getattr(data, "id", None),
        "parent_id": safe_getattr(data, "parent_id", None),
        "thumbnail_id": safe_getattr(data, "thumbnail_id", None),
        "status": safe_getattr(data, "status", "DRAFT"),
        "sort_order": safe_getattr(data, "sort_order", 0),
        "is_visible": safe_getattr(data, "is_visible", True),
        "is_weekly_schedule": safe_getattr(data, "is_weekly_schedule", False),
        "is_locked": safe_getattr(data, "is_locked", False),
        "article_count": safe_getattr(data, "article_count", 0),
        "is_translated": is_translated,
        "translations": translations_dict,
        "name": safe_getattr(data, "name", ""),
        "slug": safe_getattr(data, "slug", ""),
        "description": safe_getattr(data, "description", None),
        "seo_title": safe_getattr(data, "seo_title", None),
        "seo_description": safe_getattr(data, "seo_description", None),
        "children": safe_getattr(data, "children", [])
    }
    return db_dict


class TranslationItemResponse(BaseModel):
    """Schema cho từng bản dịch của danh mục."""
    name: str
    slug: str
    description: Optional[str] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CategoryCreate(BaseModel):
    """Request body tạo danh mục mới."""
    parent_id: Optional[uuid.UUID] = Field(default=None, description="ID danh mục cha (NULL = root)")
    thumbnail_id: Optional[uuid.UUID] = Field(default=None, description="ID ảnh đại diện trong Media Library")
    sort_order: int = Field(default=0, description="Thứ tự sắp xếp (10, 20, 30...)")
    status: str = Field(default="ACTIVE", description="Trạng thái vòng đời (ACTIVE, INACTIVE)")
    is_visible: bool = Field(default=True, description="Hiển thị ngoài website")
    is_weekly_schedule: bool = Field(default=False, description="Đánh dấu danh mục là lịch tuần")
    is_locked: bool = Field(default=False, description="Đánh dấu danh mục hệ thống không được xóa")
    translations: dict[str, TranslationItemResponse] = Field(..., description="Bản dịch của danh mục")

    @field_validator("parent_id", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: Any) -> Any:
        if v == "":
            return None
        return v


class CategoryUpdate(BaseModel):
    """Request body cập nhật danh mục."""
    parent_id: Optional[uuid.UUID] = None
    thumbnail_id: Optional[uuid.UUID] = None
    sort_order: Optional[int] = None
    status: Optional[str] = None
    is_visible: Optional[bool] = None
    is_weekly_schedule: Optional[bool] = None
    is_locked: Optional[bool] = None
    translations: Optional[dict[str, TranslationItemResponse]] = None

    @field_validator("parent_id", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: Any) -> Any:
        if v == "":
            return None
        return v


class CategoryReorderItem(BaseModel):
    """Một item thay đổi vị trí kéo thả."""
    id: uuid.UUID
    parent_id: Optional[uuid.UUID] = None
    sort_order: int = Field(..., ge=0, description="Mức sắp xếp mới (10, 15, 20...)")

    @field_validator("parent_id", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: Any) -> Any:
        if v == "":
            return None
        return v


class CategoryReorderRequest(BaseModel):
    """Request batch update kéo thả cấu trúc cây danh mục."""
    items: list[CategoryReorderItem] = Field(
        ..., min_length=1, description="Danh sách các danh mục cần dịch chuyển"
    )


class CategorySlugCheckResponse(BaseModel):
    """Phản hồi kiểm tra trùng lặp slug."""
    exists: bool = Field(..., description="Slug có trùng lặp trong hệ thống (kể cả đã xóa mềm) hay không")
    suggested_slug: str = Field(..., description="Gợi ý slug mới không bị trùng")
