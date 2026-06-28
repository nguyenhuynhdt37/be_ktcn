import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class AuditLogResponse(BaseModel):
    """
    Response schema for a single audit log entry.
    """
    id: uuid.UUID
    actor_id: uuid.UUID | None
    actor_username: str
    action: str
    target_type: str
    target_id: uuid.UUID | None
    changes: dict[str, Any] | None
    ip_address: str | None
    user_agent: str | None
    created_at: datetime


class AuditLogListResponse(BaseModel):
    """
    Paginated response schema for audit logs.
    """
    items: list[AuditLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
