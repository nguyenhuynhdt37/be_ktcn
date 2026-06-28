import uuid
from typing import List, Optional
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.models.base import BaseModel


class MediaItem(BaseModel):
    """
    Database model representing a file metadata or a directory structure.
    """
    __tablename__ = "media_items"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_folder: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("media_items.id", ondelete="CASCADE"), nullable=True
    )
    
    # Storage and metadata fields (NULL for folders)
    object_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    thumbnail_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    bucket: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    checksum: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships
    parent: Mapped[Optional["MediaItem"]] = relationship(
        "MediaItem", remote_side="MediaItem.id", back_populates="children"
    )
    children: Mapped[List["MediaItem"]] = relationship(
        "MediaItem", back_populates="parent", cascade="all, delete-orphan"
    )
