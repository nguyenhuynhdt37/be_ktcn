import enum
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.models.base import Base, BaseModel
from app.modules.language.models import Language


class ArticleStatus(str, enum.Enum):
    """
    Trạng thái của bài viết trong hệ thống CMS.
    """
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    SCHEDULED = "SCHEDULED"
    ARCHIVED = "ARCHIVED"


class ArticleTag(Base):
    """
    Bảng trung gian quản lý mối quan hệ nhiều-nhiều giữa articles và tags.
    """
    __tablename__ = "article_tags"

    article_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Index tối ưu hóa truy vấn tìm bài viết theo Tag
    __table_args__ = (
        Index("idx_article_tags_tag_id", "tag_id"),
    )


class Article(BaseModel):
    """
    Model đại diện cho bảng bài viết (articles).
    Chứa đầy đủ các trường thông tin bài viết, hình ảnh, trạng thái, SEO, Open Graph và thống kê.
    """
    __tablename__ = "articles"

    # Quan hệ khóa ngoại
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    author_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Hình ảnh (Chỉ lưu Object Key của MinIO)
    thumbnail_object_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    cover_object_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Trạng thái
    status: Mapped[ArticleStatus] = mapped_column(
        Enum(ArticleStatus, name="article_status", native_enum=True),
        default=ArticleStatus.DRAFT,
        nullable=False,
        index=True
    )
    is_draft: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    # Hiển thị
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Thống kê
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reading_time: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Thời gian
    publish_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expire_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Audit
    last_edited_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    # Relationships
    category: Mapped[Optional["Category"]] = relationship("Category")
    author: Mapped[Optional["User"]] = relationship("User")
    tags: Mapped[list["Tag"]] = relationship(
        "Tag",
        secondary="article_tags",
        back_populates="articles",
    )
    translations: Mapped[list["ArticleTranslation"]] = relationship(
        "ArticleTranslation",
        back_populates="article",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Composite Indexes & Table constraints
    __table_args__ = (
        # Phục vụ hiển thị tin tức mới nhất trang chủ
        Index("idx_articles_list_query", "status", "publish_at"),
        # Phục vụ hiển thị danh sách tin tức theo danh mục
        Index("idx_articles_category_query", "category_id", "status", "publish_at"),
        # Phục vụ hiển thị tin tức nổi bật và ghim đầu trang
        Index("idx_articles_featured_pinned", "status", "is_pinned", "is_featured", "publish_at"),
    )


class ArticleTranslation(BaseModel):
    """
    Model lưu trữ các bản dịch đa ngôn ngữ chi tiết của Article.
    """
    __tablename__ = "article_translations"

    article_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    language_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("languages.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    # Nội dung đa ngôn ngữ
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    excerpt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # SEO
    seo_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    seo_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    canonical_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    robots: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Open Graph
    og_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    og_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    og_image: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Relationships
    article: Mapped["Article"] = relationship("Article", back_populates="translations")
    language: Mapped["Language"] = relationship("Language")

    __table_args__ = (
        UniqueConstraint("article_id", "language_id", name="uq_article_language_unique"),
        UniqueConstraint("language_id", "slug", name="uq_article_language_slug_unique"),
        Index("ix_article_translations_article_language", "article_id", "language_id"),
        Index("ix_article_translations_language_slug", "language_id", "slug"),
    )
