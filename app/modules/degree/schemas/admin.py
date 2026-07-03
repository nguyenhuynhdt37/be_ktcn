import uuid
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, model_validator


class DegreeAdminResponse(BaseModel):
    """Response cho Admin CMS, chứa cấu trúc translations đầy đủ."""
    id: uuid.UUID
    sort_order: int
    is_active: bool
    translations: dict[str, Any] = {}
    name: Optional[str] = None
    abbreviation: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_translations(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return data
        
        # Chuyển đổi list translations sang dict
        trans_dict = {}
        raw_trans = getattr(data, "translations", []) or []
        for t in raw_trans:
            lang_code = t.language.code if getattr(t, "language", None) else None
            if lang_code:
                trans_dict[lang_code] = {
                    "name": t.name,
                    "abbreviation": t.abbreviation
                }
        
        # Dịch phẳng tên theo default "vi" để hiển thị mặc định
        matched = None
        for t in raw_trans:
            if t.language.code == "vi":
                matched = t
                break
        if not matched and raw_trans:
            matched = raw_trans[0]
            
        return {
            "id": data.id,
            "sort_order": data.sort_order,
            "is_active": data.is_active,
            "translations": trans_dict,
            "name": matched.name if matched else None,
            "abbreviation": matched.abbreviation if matched else None
        }
