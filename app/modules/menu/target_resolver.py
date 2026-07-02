"""
Generic Target Resolver cho Menu Item Polymorphic Association.

Thiết kế theo Strategy Pattern: mỗi target_type đăng ký 1 resolver riêng.
Khi mở rộng thêm PAGE, ARTICLE, DOCUMENT... → chỉ cần thêm 1 hàm resolve + register.
"""
import uuid
from typing import Callable, Awaitable, Optional

from loguru import logger
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException


class TargetInfo(BaseModel):
    """Thông tin target đã resolve, gắn kèm response của MenuItemResponse/TreeNode."""

    id: str
    type: str
    name: str
    slug: Optional[str] = None
    status: Optional[str] = None
    path: Optional[str] = None  # breadcrumb path, VD: "Tin tức / Tuyển sinh"
    is_weekly_schedule: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


# Type alias cho resolver function
ResolverFunc = Callable[[AsyncSession, uuid.UUID, str], Awaitable[TargetInfo]]
ValidatorFunc = Callable[[AsyncSession, uuid.UUID], Awaitable[None]]
BatchResolverFunc = Callable[[AsyncSession, list[uuid.UUID], str], Awaitable[dict[uuid.UUID, TargetInfo]]]


class TargetResolverRegistry:
    """
    Registry trung tâm quản lý các resolver theo target_type.
    Đăng ký resolver qua phương thức register(), sau đó gọi validate/resolve/batch_resolve.
    """

    def __init__(self) -> None:
        self._validators: dict[str, ValidatorFunc] = {}
        self._resolvers: dict[str, ResolverFunc] = {}
        self._batch_resolvers: dict[str, BatchResolverFunc] = {}

    def register(
        self,
        target_type: str,
        *,
        validator: ValidatorFunc,
        resolver: ResolverFunc,
        batch_resolver: BatchResolverFunc,
    ) -> None:
        """Đăng ký bộ validator + resolver + batch_resolver cho một target_type."""
        self._validators[target_type] = validator
        self._resolvers[target_type] = resolver
        self._batch_resolvers[target_type] = batch_resolver
        logger.debug(f"Registered target resolver for type: {target_type}")

    async def validate(self, db: AsyncSession, target_type: str, target_id: uuid.UUID) -> None:
        """Validate target tồn tại và đang ở trạng thái hợp lệ (ACTIVE, chưa xóa mềm...)."""
        validator = self._validators.get(target_type)
        if not validator:
            logger.warning(f"No validator registered for target_type: {target_type}")
            return  # Không block — cho phép target_type chưa có resolver (forward-compatible)
        await validator(db, target_id)

    async def resolve(self, db: AsyncSession, target_type: str, target_id: uuid.UUID, lang: str = "vi") -> Optional[TargetInfo]:
        """Resolve thông tin chi tiết của 1 target."""
        resolver = self._resolvers.get(target_type)
        if not resolver:
            return None
        try:
            return await resolver(db, target_id, lang)
        except Exception:
            logger.warning(f"Failed to resolve target: type={target_type}, id={target_id}")
            return None

    async def batch_resolve(
        self, db: AsyncSession, targets: list[tuple[str, uuid.UUID]], lang: str = "vi"
    ) -> dict[uuid.UUID, TargetInfo]:
        """
        Batch resolve nhiều targets cùng lúc, nhóm theo target_type để tối ưu query.
        Input: list[(target_type, target_id)]
        Output: dict[target_id -> TargetInfo]
        """
        # Nhóm target_ids theo target_type
        grouped: dict[str, list[uuid.UUID]] = {}
        for t_type, t_id in targets:
            grouped.setdefault(t_type, []).append(t_id)

        result: dict[uuid.UUID, TargetInfo] = {}

        for t_type, t_ids in grouped.items():
            batch_resolver = self._batch_resolvers.get(t_type)
            if batch_resolver:
                try:
                    resolved = await batch_resolver(db, t_ids, lang)
                    result.update(resolved)
                except Exception as e:
                    logger.warning(f"Batch resolve failed for type={t_type}: {e}")

        return result


# ──────────────────────────────────────────────
# Category Resolver Implementation
# ──────────────────────────────────────────────


async def _validate_category(db: AsyncSession, target_id: uuid.UUID) -> None:
    """Validate Category tồn tại, chưa bị xóa mềm, và đang ở trạng thái ACTIVE."""
    from app.modules.category.models import Category

    query = select(Category).where(Category.id == target_id)
    result = await db.execute(query)
    category = result.scalar_one_or_none()

    if not category:
        raise NotFoundException(
            message="Danh mục được liên kết không tồn tại",
            error_code="TARGET_CATEGORY_NOT_FOUND",
            details={"target_id": str(target_id)},
        )

    if category.deleted_at is not None:
        raise BadRequestException(
            message="Danh mục được liên kết đã bị xóa",
            error_code="TARGET_CATEGORY_DELETED",
            details={"target_id": str(target_id), "name": category.name},
        )

    if category.status != "ACTIVE":
        raise BadRequestException(
            message=f"Danh mục '{category.name}' đang ở trạng thái '{category.status}'. Chỉ cho phép liên kết với danh mục đang hoạt động (ACTIVE).",
            error_code="TARGET_CATEGORY_NOT_ACTIVE",
            details={"target_id": str(target_id), "status": category.status},
        )


async def _resolve_category(db: AsyncSession, target_id: uuid.UUID, lang: str = "vi") -> TargetInfo:
    """Resolve thông tin chi tiết của một Category (bao gồm breadcrumb path)."""
    from app.modules.category.models import Category
    from app.modules.category.service import category_service

    query = select(Category).where(Category.id == target_id, Category.deleted_at == None)
    result = await db.execute(query)
    category = result.scalar_one_or_none()

    if not category:
        return TargetInfo(id=str(target_id), type="CATEGORY", name="[Đã xóa]", status="DELETED")

    # Dịch category hiện tại
    category_service._apply_translation(category, lang=lang)

    # Build breadcrumb path bằng cách truy ngược parent chain
    path_parts = [category.name]
    current_parent_id = category.parent_id
    visited: set[uuid.UUID] = {category.id}
    max_depth = 10  # Tránh vòng lặp vô hạn

    while current_parent_id and len(path_parts) < max_depth:
        if current_parent_id in visited:
            break
        visited.add(current_parent_id)

        parent_query = select(Category).where(
            Category.id == current_parent_id, Category.deleted_at == None
        )
        parent_result = await db.execute(parent_query)
        parent_row = parent_result.scalar_one_or_none()

        if not parent_row:
            break

        # Dịch parent row trước khi lấy name
        category_service._apply_translation(parent_row, lang=lang)
        path_parts.insert(0, parent_row.name)
        current_parent_id = parent_row.parent_id

    return TargetInfo(
        id=str(category.id),
        type="CATEGORY",
        name=category.name,
        slug=category.slug,
        status=category.status,
        path=" / ".join(path_parts),
        is_weekly_schedule=category.is_weekly_schedule,
    )


async def _batch_resolve_categories(db: AsyncSession, target_ids: list[uuid.UUID], lang: str = "vi") -> dict[uuid.UUID, TargetInfo]:
    """
    Batch resolve nhiều categories cùng lúc bằng 1 câu IN query duy nhất.
    Sau đó build breadcrumb path cho từng category.
    """
    from app.modules.category.models import Category
    from app.modules.category.service import category_service

    if not target_ids:
        return {}

    # 1. Query tất cả categories liên quan (bao gồm cả parents tiềm năng)
    query = select(Category).where(Category.deleted_at == None)
    result = await db.execute(query)
    all_categories = {c.id: c for c in result.scalars().all()}

    # Áp dụng dịch cho tất cả categories trong map
    for cat in all_categories.values():
        category_service._apply_translation(cat, lang=lang)

    resolved: dict[uuid.UUID, TargetInfo] = {}

    for t_id in target_ids:
        cat = all_categories.get(t_id)
        if not cat:
            resolved[t_id] = TargetInfo(id=str(t_id), type="CATEGORY", name="[Đã xóa]", status="DELETED")
            continue

        # Build breadcrumb path in-memory (đã có tất cả categories trong bộ nhớ và đã dịch)
        path_parts = [cat.name]
        current_parent_id = cat.parent_id
        visited: set[uuid.UUID] = {cat.id}
        max_depth = 10

        while current_parent_id and len(path_parts) < max_depth:
            if current_parent_id in visited:
                break
            visited.add(current_parent_id)
            parent = all_categories.get(current_parent_id)
            if not parent:
                break
            path_parts.insert(0, parent.name)
            current_parent_id = parent.parent_id

        resolved[t_id] = TargetInfo(
            id=str(cat.id),
            type="CATEGORY",
            name=cat.name,
            slug=cat.slug,
            status=cat.status,
            path=" / ".join(path_parts),
            is_weekly_schedule=cat.is_weekly_schedule,
        )

    return resolved


# ──────────────────────────────────────────────
# Article Resolver Implementation
# ──────────────────────────────────────────────


async def _validate_article(db: AsyncSession, target_id: uuid.UUID) -> None:
    """Validate Article tồn tại, chưa bị xóa mềm, và đang ở trạng thái PUBLISHED."""
    from app.modules.article.models import Article, ArticleStatus

    query = select(Article).where(Article.id == target_id)
    result = await db.execute(query)
    article = result.scalar_one_or_none()

    if not article:
        raise NotFoundException(
            message="Bài viết được liên kết không tồn tại",
            error_code="TARGET_ARTICLE_NOT_FOUND",
            details={"target_id": str(target_id)},
        )

    if article.deleted_at is not None:
        raise BadRequestException(
            message="Bài viết được liên kết đã bị xóa",
            error_code="TARGET_ARTICLE_DELETED",
            details={"target_id": str(target_id), "title": article.title},
        )

    status_val = article.status.value if hasattr(article.status, 'value') else article.status
    if status_val != ArticleStatus.PUBLISHED.value:
        raise BadRequestException(
            message=f"Bài viết '{article.title}' đang ở trạng thái '{status_val}'. Chỉ cho phép liên kết với bài viết đã xuất bản (PUBLISHED).",
            error_code="TARGET_ARTICLE_NOT_PUBLISHED",
            details={"target_id": str(target_id), "status": status_val},
        )


async def _resolve_article(db: AsyncSession, target_id: uuid.UUID, lang: str = "vi") -> TargetInfo:
    """Resolve thông tin chi tiết của một Article."""
    from app.modules.article.models import Article

    query = select(Article).where(Article.id == target_id, Article.deleted_at == None)
    result = await db.execute(query)
    article = result.scalar_one_or_none()

    if not article:
        return TargetInfo(id=str(target_id), type="ARTICLE", name="[Đã xóa]", status="DELETED")

    status_val = article.status.value if hasattr(article.status, 'value') else article.status
    return TargetInfo(
        id=str(article.id),
        type="ARTICLE",
        name=article.title,
        slug=article.slug,
        status=status_val,
        path=f"/tin-tuc/{article.slug}",
    )


async def _batch_resolve_articles(db: AsyncSession, target_ids: list[uuid.UUID], lang: str = "vi") -> dict[uuid.UUID, TargetInfo]:
    """Batch resolve nhiều articles cùng lúc bằng 1 câu IN query."""
    from app.modules.article.models import Article

    if not target_ids:
        return {}

    query = select(Article).where(Article.id.in_(target_ids), Article.deleted_at == None)
    result = await db.execute(query)
    articles = {a.id: a for a in result.scalars().all()}

    resolved: dict[uuid.UUID, TargetInfo] = {}
    for t_id in target_ids:
        art = articles.get(t_id)
        if not art:
            resolved[t_id] = TargetInfo(id=str(t_id), type="ARTICLE", name="[Đã xóa]", status="DELETED")
            continue

        status_val = art.status.value if hasattr(art.status, 'value') else art.status
        resolved[t_id] = TargetInfo(
            id=str(art.id),
            type="ARTICLE",
            name=art.title,
            slug=art.slug,
            status=status_val,
            path=f"/tin-tuc/{art.slug}",
        )
    return resolved


# ──────────────────────────────────────────────
# Department Resolver Implementation
# ──────────────────────────────────────────────


async def _validate_department(db: AsyncSession, target_id: uuid.UUID) -> None:
    """Validate Department tồn tại, chưa bị xóa mềm, và đang hoạt động (is_active=True)."""
    from app.modules.department.models import Department
    from app.modules.department.service import department_service

    query = select(Department).where(Department.id == target_id)
    result = await db.execute(query)
    dept = result.scalar_one_or_none()

    if not dept:
        raise NotFoundException(
            message="Bộ môn được liên kết không tồn tại",
            error_code="TARGET_DEPARTMENT_NOT_FOUND",
            details={"target_id": str(target_id)},
        )

    if dept.deleted_at is not None:
        raise BadRequestException(
            message="Bộ môn được liên kết đã bị xóa",
            error_code="TARGET_DEPARTMENT_DELETED",
            details={"target_id": str(target_id)},
        )

    department_service._apply_translation(dept, lang="vi")
    if not dept.is_active:
        raise BadRequestException(
            message=f"Bộ môn '{dept.name}' đang ở trạng thái ngưng hoạt động. Chỉ cho phép liên kết với bộ môn đang hoạt động.",
            error_code="TARGET_DEPARTMENT_NOT_ACTIVE",
            details={"target_id": str(target_id)},
        )


async def _resolve_department(db: AsyncSession, target_id: uuid.UUID, lang: str = "vi") -> TargetInfo:
    """Resolve thông tin chi tiết của một Department."""
    from app.modules.department.models import Department
    from app.modules.department.service import department_service

    query = select(Department).where(Department.id == target_id, Department.deleted_at == None)
    result = await db.execute(query)
    dept = result.scalar_one_or_none()

    if not dept:
        return TargetInfo(id=str(target_id), type="DEPARTMENT", name="[Đã xóa]", status="DELETED")

    department_service._apply_translation(dept, lang=lang)
    return TargetInfo(
        id=str(dept.id),
        type="DEPARTMENT",
        name=dept.name,
        slug=dept.slug,
        status="ACTIVE" if dept.is_active else "INACTIVE",
        path=f"/bo-mon/{dept.slug}",
    )


async def _batch_resolve_departments(db: AsyncSession, target_ids: list[uuid.UUID], lang: str = "vi") -> dict[uuid.UUID, TargetInfo]:
    """Batch resolve nhiều departments cùng lúc bằng 1 câu IN query."""
    from app.modules.department.models import Department
    from app.modules.department.service import department_service

    if not target_ids:
        return {}

    query = select(Department).where(Department.id.in_(target_ids), Department.deleted_at == None)
    result = await db.execute(query)
    departments = {d.id: d for d in result.scalars().all()}

    resolved: dict[uuid.UUID, TargetInfo] = {}
    for t_id in target_ids:
        dept = departments.get(t_id)
        if not dept:
            resolved[t_id] = TargetInfo(id=str(t_id), type="DEPARTMENT", name="[Đã xóa]", status="DELETED")
            continue

        department_service._apply_translation(dept, lang=lang)
        resolved[t_id] = TargetInfo(
            id=str(dept.id),
            type="DEPARTMENT",
            name=dept.name,
            slug=dept.slug,
            status="ACTIVE" if dept.is_active else "INACTIVE",
            path=f"/bo-mon/{dept.slug}",
        )
    return resolved


# ──────────────────────────────────────────────
# Page Resolver (Mock/Future-proof)
# ──────────────────────────────────────────────


async def _validate_page(db: AsyncSession, target_id: uuid.UUID) -> None:
    """Validate Page (Mock vì chưa có module Page)."""
    logger.warning(f"Static pages module is not implemented yet. Skipping validation for page: {target_id}")
    return


async def _resolve_page(db: AsyncSession, target_id: uuid.UUID, lang: str = "vi") -> TargetInfo:
    """Resolve Page (Mock)."""
    return TargetInfo(
        id=str(target_id),
        type="PAGE",
        name=f"[Trang tĩnh {str(target_id)[:8]}]",
        path=f"/page/{target_id}",
        status="ACTIVE",
    )


async def _batch_resolve_pages(db: AsyncSession, target_ids: list[uuid.UUID], lang: str = "vi") -> dict[uuid.UUID, TargetInfo]:
    """Batch resolve Pages (Mock)."""
    return {t_id: await _resolve_page(db, t_id, lang) for t_id in target_ids}


# ──────────────────────────────────────────────
# Global Registry Instance
# ──────────────────────────────────────────────

target_resolver = TargetResolverRegistry()

# Đăng ký Category resolver
target_resolver.register(
    "CATEGORY",
    validator=_validate_category,
    resolver=_resolve_category,
    batch_resolver=_batch_resolve_categories,
)

# Đăng ký Article resolver
target_resolver.register(
    "ARTICLE",
    validator=_validate_article,
    resolver=_resolve_article,
    batch_resolver=_batch_resolve_articles,
)

# Đăng ký Department resolver
target_resolver.register(
    "DEPARTMENT",
    validator=_validate_department,
    resolver=_resolve_department,
    batch_resolver=_batch_resolve_departments,
)

# Đăng ký Page resolver
target_resolver.register(
    "PAGE",
    validator=_validate_page,
    resolver=_resolve_page,
    batch_resolver=_batch_resolve_pages,
)
