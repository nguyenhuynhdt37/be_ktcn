from __future__ import annotations
import uuid
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.modules.menu.models import MenuItemTargetType


def safe_getattr(obj: Any, attr: str, default: Any = None) -> Any:
    """Truy cập thuộc tính của đối tượng một cách an toàn, tránh kích hoạt AttributeError/MissingGreenlet của SQLAlchemy mapper."""
    if not obj:
        return default
    if isinstance(obj, dict):
        return obj.get(attr, default)
    if hasattr(obj, "__dict__") and attr in obj.__dict__:
        return obj.__dict__[attr]
    if attr in ["children", "translations", "items"]:
        return default
    try:
        return getattr(obj, attr, default)
    except AttributeError:
        return default


def build_menu_item_resolved(data: Any) -> Any:
    """Helper chuyển đổi đối tượng MenuItem (ORM hoặc dict) để xử lý translations của menu item."""
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
        if "children" not in data:
            data["children"] = []
        return data

    translations_dict = {
        "vi": {"title": "", "is_translated": False},
        "en": {"title": "", "is_translated": False}
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
                    "is_translated": True
                }
                is_translated[lang_code] = True

    db_dict = {
        "id": safe_getattr(data, "id", None),
        "menu_id": safe_getattr(data, "menu_id", None),
        "parent_id": safe_getattr(data, "parent_id", None),
        "target_type": safe_getattr(data, "target_type", None),
        "target_id": safe_getattr(data, "target_id", None),
        "external_url": safe_getattr(data, "external_url", None),
        "open_in_new_tab": safe_getattr(data, "open_in_new_tab", False),
        "depth": safe_getattr(data, "depth", 1),
        "sort_order": safe_getattr(data, "sort_order", 0),
        "is_visible": safe_getattr(data, "is_visible", True),
        "is_translated": is_translated,
        "translations": translations_dict,
        "title": safe_getattr(data, "title", ""),
        "children": safe_getattr(data, "children", [])
    }
    return db_dict


class TranslationItemResponse(BaseModel):
    """Schema cho từng bản dịch của MenuItem."""
    title: str

    model_config = ConfigDict(from_attributes=True)


class MenuCreate(BaseModel):
    """Payload tạo mới một menu."""
    name: str = Field(..., max_length=100, description="Tên khu vực menu (ví dụ: Header Main)")
    code: str = Field(..., max_length=50, description="Mã duy nhất (ví dụ: header_main)")
    description: Optional[str] = None
    is_active: bool = True


class MenuUpdate(BaseModel):
    """Payload cập nhật thông tin menu."""
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class MenuItemCreate(BaseModel):
    """Payload tạo MenuItem."""
    parent_id: Optional[uuid.UUID] = None
    target_type: Optional[MenuItemTargetType] = None
    target_id: Optional[uuid.UUID] = None
    external_url: Optional[str] = None
    open_in_new_tab: bool = False
    sort_order: int = 0
    is_visible: bool = True
    translations: dict[str, TranslationItemResponse] = Field(..., description="Bản dịch của menu item")

    @field_validator("parent_id", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: Any) -> Any:
        if v == "":
            return None
        return v


class MenuItemUpdate(BaseModel):
    """Payload cập nhật MenuItem."""
    parent_id: Optional[uuid.UUID] = None
    target_type: Optional[MenuItemTargetType] = None
    target_id: Optional[uuid.UUID] = None
    external_url: Optional[str] = None
    open_in_new_tab: Optional[bool] = None
    sort_order: Optional[int] = None
    is_visible: Optional[bool] = None
    translations: Optional[dict[str, TranslationItemResponse]] = None

    @field_validator("parent_id", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: Any) -> Any:
        if v == "":
            return None
        return v


class MenuItemReorderItem(BaseModel):
    """Item reorder trong danh sách."""
    id: uuid.UUID
    parent_id: Optional[uuid.UUID] = None
    sort_order: int

    @field_validator("parent_id", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: Any) -> Any:
        if v == "":
            return None
        return v


class MenuItemReorderRequest(BaseModel):
    """Request batch update vị trí các menu items."""
    items: list[MenuItemReorderItem]
