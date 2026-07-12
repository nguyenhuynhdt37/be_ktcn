import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.modules.notification.models import NotificationType


class NotificationResponse(BaseModel):
    id: uuid.UUID
    recipient_id: uuid.UUID
    type: NotificationType
    title: str
    message: str | None = None
    related_entity_type: str | None = None
    related_entity_id: uuid.UUID | None = None
    related_url: str | None = None
    read_at: datetime | None = None
    created_at: datetime
    details: dict | None = None

    model_config = ConfigDict(from_attributes=True)


class NotificationPaginationResponse(BaseModel):
    items: list[NotificationResponse]
    page: int
    page_size: int
    total_items: int
    total_pages: int
    unread_count: int
    has_next: bool
    has_previous: bool


class UnreadCountResponse(BaseModel):
    unread_count: int


class MarkAllReadResponse(BaseModel):
    updated_count: int
