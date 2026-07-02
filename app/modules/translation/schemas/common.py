from enum import Enum
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

class TranslationContext(str, Enum):
    MENU_NAME = "menu_name"
    CATEGORY_NAME = "category_name"
    SHORT_DESCRIPTION = "short_description"
    DEPARTMENT_NAME = "department_name"
    DEPARTMENT_DESCRIPTION = "department_description"
    POSITION_NAME = "position_name"
    POSITION_DESCRIPTION = "position_description"
    ENGLISH_NAME = "english_name"
    RESEARCH_DIRECTION = "research_direction"
    ARTICLE_TITLE = "article_title"
    ARTICLE_SUMMARY = "article_summary"
    SCIENTIFIC_PROFILE = "scientific_profile"
    ARTICLE_CONTENT = "article_content"

class TranslationRequest(BaseModel):
    text: str = Field(..., description="Văn bản tiếng Việt cần dịch")
    target_languages: List[str] = Field(
        default=["en"], 
        description="Danh sách ngôn ngữ đích cần dịch (chỉ hỗ trợ 'en')"
    )
    context: Optional[TranslationContext] = Field(
        default=None,
        description="Ngữ cảnh dịch để định hướng dịch chính xác"
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
    context: Optional[TranslationContext] = Field(
        default=None,
        description="Ngữ cảnh dịch để định hướng dịch chính xác"
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
    context: Optional[TranslationContext] = Field(
        default=None,
        description="Ngữ cảnh dịch để định hướng dịch chính xác"
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
