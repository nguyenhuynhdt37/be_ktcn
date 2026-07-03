"""
Global Search API — Tìm kiếm nhanh đa nguồn dữ liệu.
Endpoint: GET /api/v1/admin/search?q=keyword&limit=5
"""
import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserResponse

# Models
from app.modules.article.models import Article, ArticleTranslation
from app.modules.auth.models import User
from app.modules.category.models import Category
from app.modules.tag.models import Tag, TagTranslation
from app.modules.staff.models import Staff

router = APIRouter()


async def _search_articles(db: AsyncSession, keyword: str, limit: int) -> list[dict]:
    """Tìm bài viết theo title trong ArticleTranslation. DISTINCT ON article_id để tránh trùng."""
    from app.modules.category.models import CategoryTranslation

    stmt = (
        select(
            Article.id,
            ArticleTranslation.title,
            ArticleTranslation.slug,
            Article.status,
            Article.published_at,
            CategoryTranslation.name.label("category_name"),
        )
        .join(ArticleTranslation, ArticleTranslation.article_id == Article.id)
        .outerjoin(Category, Category.id == Article.category_id)
        .outerjoin(
            CategoryTranslation,
            (CategoryTranslation.category_id == Category.id),
        )
        .where(
            Article.deleted_at.is_(None),
            ArticleTranslation.title.ilike(f"%{keyword}%"),
        )
        .distinct(Article.id)
        .order_by(Article.id, Article.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return [
        {
            "id": str(r.id),
            "title": r.title,
            "slug": r.slug,
            "status": r.status.value if hasattr(r.status, 'value') else r.status,
            "category_name": r.category_name,
            "published_at": r.published_at.isoformat() if r.published_at else None,
        }
        for r in result.all()
    ]


async def _search_users(db: AsyncSession, keyword: str, limit: int) -> list[dict]:
    """Tìm user theo full_name, username, email."""
    stmt = (
        select(User.id, User.full_name, User.email, User.username)
        .where(
            User.deleted_at.is_(None),
            (
                User.full_name.ilike(f"%{keyword}%")
                | User.username.ilike(f"%{keyword}%")
                | User.email.ilike(f"%{keyword}%")
            ),
        )
        .order_by(User.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return [
        {"id": str(r.id), "full_name": r.full_name, "email": r.email, "username": r.username}
        for r in result.all()
    ]


async def _search_categories(db: AsyncSession, keyword: str, limit: int) -> list[dict]:
    """Tìm danh mục qua CategoryTranslation. DISTINCT ON category_id."""
    from app.modules.category.models import CategoryTranslation

    stmt = (
        select(Category.id, CategoryTranslation.name, CategoryTranslation.slug)
        .join(CategoryTranslation, CategoryTranslation.category_id == Category.id)
        .where(
            Category.deleted_at.is_(None),
            CategoryTranslation.name.ilike(f"%{keyword}%"),
        )
        .distinct(Category.id)
        .order_by(Category.id, Category.sort_order)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return [
        {"id": str(r.id), "name": r.name, "slug": r.slug}
        for r in result.all()
    ]


async def _search_tags(db: AsyncSession, keyword: str, limit: int) -> list[dict]:
    """Tìm tag qua TagTranslation. DISTINCT ON tag_id."""
    stmt = (
        select(Tag.id, TagTranslation.name, TagTranslation.slug)
        .join(TagTranslation, TagTranslation.tag_id == Tag.id)
        .where(
            Tag.deleted_at.is_(None),
            TagTranslation.name.ilike(f"%{keyword}%"),
        )
        .distinct(Tag.id)
        .order_by(Tag.id, Tag.sort_order)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return [
        {"id": str(r.id), "name": r.name, "slug": r.slug}
        for r in result.all()
    ]


async def _search_staff(db: AsyncSession, keyword: str, limit: int) -> list[dict]:
    """Tìm nhân sự theo full_name, email."""
    stmt = (
        select(Staff.id, Staff.full_name, Staff.email, Staff.slug)
        .where(
            Staff.deleted_at.is_(None),
            (
                Staff.full_name.ilike(f"%{keyword}%")
                | Staff.email.ilike(f"%{keyword}%")
            ),
        )
        .order_by(Staff.sort_order)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return [
        {"id": str(r.id), "full_name": r.full_name, "email": r.email, "slug": r.slug}
        for r in result.all()
    ]


@router.get("")
async def global_search(
    q: str = Query(..., min_length=1, max_length=100, description="Từ khóa tìm kiếm"),
    limit: int = Query(default=5, ge=1, le=20, description="Số kết quả mỗi nhóm"),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Tìm kiếm nhanh đa nguồn: bài viết, thành viên, danh mục, tags, nhân sự.
    Chạy song song tất cả các query bằng asyncio.gather().
    """
    keyword = q.strip()
    if not keyword:
        return {"articles": [], "users": [], "categories": [], "tags": [], "staff": []}

    articles, users, categories, tags, staff = await asyncio.gather(
        _search_articles(db, keyword, limit),
        _search_users(db, keyword, limit),
        _search_categories(db, keyword, limit),
        _search_tags(db, keyword, limit),
        _search_staff(db, keyword, limit),
    )

    return {
        "articles": articles,
        "users": users,
        "categories": categories,
        "tags": tags,
        "staff": staff,
    }
