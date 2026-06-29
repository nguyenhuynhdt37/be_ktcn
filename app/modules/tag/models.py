import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.models.base import BaseModel


class Tag(BaseModel):
    """
    Model đại diện cho Tag dùng chung trong hệ thống CMS.
    Hỗ trợ gán nhãn cho nhiều thực thể (Article, Page, v.v.).
    """
    __tablename__ = "tags"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)  # Mã HEX, ví dụ: #FF5733
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    # Soft delete support
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True, index=True
    )

    articles: Mapped[list["Article"]] = relationship(
        "Article",
        secondary="article_tags",
        back_populates="tags"
    )
