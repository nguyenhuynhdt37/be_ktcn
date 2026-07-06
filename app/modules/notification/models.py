import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.models.base import BaseModel


class NotificationType(str, enum.Enum):
    CONSULTATION_CREATED = "CONSULTATION_CREATED"
    APPLICATION_CREATED = "APPLICATION_CREATED"
    CONTACT_CREATED = "CONTACT_CREATED"
    ACTION_REQUIRED = "ACTION_REQUIRED"


class Notification(BaseModel):
    __tablename__ = "notifications"

    recipient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, name="notification_type"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    related_entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    related_entity_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    related_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    department_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    recipient = relationship("User", foreign_keys=[recipient_id])

    __table_args__ = (
        Index("idx_notifications_recipient_created", "recipient_id", "created_at"),
        Index("idx_notifications_recipient_unread", "recipient_id", "read_at"),
    )
