import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime, Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.models.base import BaseModel
from app.modules.media.models import MediaItem


class Language(BaseModel):
    """
    Model đại diện cho Ngôn ngữ trong hệ thống CMS.
    """
    __tablename__ = "languages"

    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    native_name: Mapped[str] = mapped_column(String(100), nullable=False)
    flag_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("media_items.id", ondelete="SET NULL"), nullable=True
    )
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)

    # Relationships
    flag: Mapped[Optional[MediaItem]] = relationship(
        MediaItem, foreign_keys=[flag_id]
    )

    # Soft delete support
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True, index=True
    )
