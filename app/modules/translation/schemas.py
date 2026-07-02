from pydantic import BaseModel, Field, field_validator
from typing import List, Any, Dict, Optional


class TranslationRequest(BaseModel):
    text: str = Field(..., description="Văn bản tiếng Việt cần dịch")
    target_languages: List[str] = Field(
        default=["en"], 
        description="Danh sách ngôn ngữ đích cần dịch (chỉ hỗ trợ 'en')"
    )

    @field_validator("target_languages")
    @classmethod
    def validate_languages(cls, v: List[str]) -> List[str]:
        allowed = {"en"}
        invalid = [lang for lang in v if lang not in allowed]
        if invalid:
            raise ValueError(f"Ngôn ngữ đích không hợp lệ: {invalid}. Chỉ hỗ trợ 'en'.")
        if not v:
            raise ValueError("Danh sách ngôn ngữ đích không được rỗng.")
        return list(set(v))


class BatchTranslationRequest(BaseModel):
    texts: List[str] = Field(..., description="Danh sách các đoạn văn bản tiếng Việt cần dịch")
    target_languages: List[str] = Field(
        default=["en"],
        description="Danh sách ngôn ngữ đích cần dịch (chỉ hỗ trợ 'en')"
    )

    @field_validator("target_languages")
    @classmethod
    def validate_languages(cls, v: List[str]) -> List[str]:
        allowed = {"en"}
        invalid = [lang for lang in v if lang not in allowed]
        if invalid:
            raise ValueError(f"Ngôn ngữ đích không hợp lệ: {invalid}. Chỉ hỗ trợ 'en'.")
        if not v:
            raise ValueError("Danh sách ngôn ngữ đích không được rỗng.")
        return list(set(v))


class HTMLTranslationRequest(BaseModel):
    html: str = Field(..., description="Nội dung chuỗi HTML cần dịch")
    target_languages: List[str] = Field(
        default=["en"],
        description="Danh sách ngôn ngữ đích cần dịch (chỉ hỗ trợ 'en')"
    )

    @field_validator("target_languages")
    @classmethod
    def validate_languages(cls, v: List[str]) -> List[str]:
        allowed = {"en"}
        invalid = [lang for lang in v if lang not in allowed]
        if invalid:
            raise ValueError(f"Ngôn ngữ đích không hợp lệ: {invalid}. Chỉ hỗ trợ 'en'.")
        if not v:
            raise ValueError("Danh sách ngôn ngữ đích không được rỗng.")
        return list(set(v))


class AISettingsUpdateRequest(BaseModel):
    active_model: str = Field(..., description="Tên model được chọn hoạt động chính")


class AISettingsResponse(BaseModel):
    active_model: str = Field(..., description="Model đang hoạt động hiện tại")
    models: List[Dict[str, Any]] = Field(..., description="Danh sách các model khả dụng")
