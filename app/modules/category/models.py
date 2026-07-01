import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.models.base import BaseModel
from app.modules.media.models import MediaItem
from app.modules.language.models import Language


class Category(BaseModel):
    """
    Model đại diện cho danh mục bài viết (Category).
    Bảng categories chỉ lưu trữ cấu hình phi ngôn ngữ, dữ liệu phân cấp cây danh mục
    và thông tin kiểm toán (audit fields). Dữ liệu hiển thị chi tiết theo từng ngôn ngữ
    sẽ được lưu trong bảng dịch category_translations.
    """
    __tablename__ = "categories"

    # Cấu hình phân cấp cây danh mục
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    
    
    # Ảnh đại diện của danh mục
    thumbnail_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("media_items.id", ondelete="SET NULL"), nullable=True
    )
    
    # Cấu hình trạng thái hiển thị & Kéo thả
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="DRAFT", nullable=False, index=True)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_weekly_schedule: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Audit log fields (người tạo, sửa, xóa)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    deleted_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    
    # Soft Delete support
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True, index=True
    )



    # Relationships (typing đầy đủ dạng Mapped)
    parent: Mapped[Optional["Category"]] = relationship(
        "Category", remote_side="Category.id", back_populates="children"
    )
    children: Mapped[list["Category"]] = relationship(
        "Category", back_populates="parent", cascade="all, delete-orphan", passive_deletes=True
    )
    thumbnail: Mapped[Optional[MediaItem]] = relationship(
        MediaItem, foreign_keys=[thumbnail_id]
    )
    
    # Quan hệ danh sách bản dịch (Eager load bằng selectin để tránh N+1 Query)
    translations: Mapped[list["CategoryTranslation"]] = relationship(
        "CategoryTranslation", back_populates="category", cascade="all, delete-orphan", lazy="selectin"
    )


class CategoryTranslation(BaseModel):
    """
    Model lưu trữ các bản dịch đa ngôn ngữ chi tiết của Category.
    
    Business Rules (Quy tắc Nghiệp vụ xử lý ở Service):
      - Một Category bắt buộc phải luôn đi kèm ít nhất một bản dịch tiếng Việt ('vi').
      - Không cho phép xóa bản dịch tiếng Việt ('vi') của danh mục.
      - Trường language_id và category_id cố định, không được phép thay đổi sau khi tạo.
      - Slug phải là độc bản trong phạm vi của một ngôn ngữ (không được trùng slug cùng ngôn ngữ).
    """
    __tablename__ = "category_translations"

    # Khóa ngoại liên kết danh mục gốc (CASCADE khi xóa danh mục)
    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    # Khóa ngoại liên kết ngôn ngữ (RESTRICT: Chặn xóa Ngôn ngữ nếu vẫn còn bản dịch)
    language_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("languages.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    # Các trường nội dung đa ngôn ngữ chi tiết
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Cấu hình SEO độc lập cho từng ngôn ngữ
    seo_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    seo_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships hai chiều (typing đầy đủ Mapped)
    category: Mapped["Category"] = relationship(
        "Category", back_populates="translations"
    )
    language: Mapped["Language"] = relationship(
        "Language", back_populates="translations"
    )

    # Ràng buộc Độc bản (Unique Constraints) & Chỉ mục (Explicit Indexes)
    __table_args__ = (
        UniqueConstraint("category_id", "language_id", name="uq_category_language_unique"),
        UniqueConstraint("language_id", "slug", name="uq_language_slug_unique"),
        
        # Bổ sung Index tường minh tối ưu hóa truy vấn tìm kiếm/phân tích URL
        Index("ix_category_translations_category_language", "category_id", "language_id"),
        Index("ix_category_translations_language_slug", "language_id", "slug"),
    )
