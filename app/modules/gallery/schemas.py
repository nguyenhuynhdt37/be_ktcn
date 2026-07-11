import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class GalleryTranslationInput(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None


class GalleryItemInput(BaseModel):
    media_item_id: uuid.UUID
    caption: Optional[str] = None
    alt_text: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True


class GalleryCreate(BaseModel):
    department_id: uuid.UUID
    cover_object_key: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True
    translations: dict[str, GalleryTranslationInput]
    items: list[GalleryItemInput] = []


class GalleryUpdate(BaseModel):
    department_id: Optional[uuid.UUID] = None
    cover_object_key: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    translations: Optional[dict[str, GalleryTranslationInput]] = None
    items: Optional[list[GalleryItemInput]] = None


class GalleryItemResponse(BaseModel):
    id: uuid.UUID
    media_item_id: uuid.UUID
    object_key: Optional[str] = None
    thumbnail_key: Optional[str] = None
    caption: Optional[str] = None
    alt_text: Optional[str] = None
    sort_order: int
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


class GalleryResponse(BaseModel):
    id: uuid.UUID
    department_id: uuid.UUID
    cover_object_key: Optional[str] = None
    sort_order: int
    is_active: bool
    title: str = ""
    description: Optional[str] = None
    translations: dict[str, Any] = {}
    items: list[GalleryItemResponse] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class GalleryPaginationResponse(BaseModel):
    items: list[GalleryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
