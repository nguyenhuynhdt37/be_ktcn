import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.models.base import BaseModel
from app.modules.media.models import MediaItem


class User(BaseModel):
    """
    Primary user entity containing credentials, logs, and state parameters.
    """
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    bio: Mapped[Optional[str]] = mapped_column(Text)
    title: Mapped[Optional[str]] = mapped_column(String(100))
    avatar_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("media_items.id", ondelete="SET NULL"), nullable=True
    )

    avatar: Mapped[Optional[MediaItem]] = relationship(MediaItem, foreign_keys=[avatar_id])

    # Soft delete support
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=None)


class RefreshToken(BaseModel):
    """
    Active JWT Refresh Token for rotation, revocation, and session auditing.
    """
    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    parent_token_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("refresh_tokens.id", ondelete="SET NULL")
    )

    user: Mapped[User] = relationship(User)


class LoginHistory(BaseModel):
    """
    History log recording login attempts and client metadata.
    """
    __tablename__ = "login_histories"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    failure_reason: Mapped[Optional[str]] = mapped_column(String(255))
