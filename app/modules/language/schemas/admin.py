import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class LanguageResponse(BaseModel):
    """
    Schema phản hồi thông tin ngôn ngữ đầy đủ phục vụ quản trị (Admin).
    """
    id: uuid.UUID
    code: str
    name: str
    native_name: str
    is_default: bool
    is_system: bool
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
