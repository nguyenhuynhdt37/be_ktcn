import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple

from loguru import logger
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.modules.category.utils import generate_slug
from app.modules.tag.models import Tag
from app.modules.tag.schemas import TagCreate, TagUpdate


class TagService:
    """
    Business logic cho quản lý Tag dùng chung.
    """

    async def list_tags(
        self,
        db: AsyncSession,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        only_has_articles: bool = False,
        page: int = 1,
        limit: int = 10,
    ) -> Tuple[list[Tag], int]:
        """
        Lấy danh sách các Tag chưa bị xóa mềm với phân trang, tìm kiếm và lọc tag có bài viết.
        """
        skip = (page - 1) * limit

        # Query đếm tổng số phần tử thỏa mãn điều kiện
        count_stmt = select(func.count(Tag.id)).where(Tag.deleted_at.is_(None))
        
        # Query lấy dữ liệu
        data_stmt = select(Tag).where(Tag.deleted_at.is_(None))

        if search:
            search_filter = Tag.name.ilike(f"%{search}%") | Tag.description.ilike(f"%{search}%")
            count_stmt = count_stmt.where(search_filter)
            data_stmt = data_stmt.where(search_filter)

        if is_active is not None:
            count_stmt = count_stmt.where(Tag.is_active == is_active)
            data_stmt = data_stmt.where(Tag.is_active == is_active)

        if only_has_articles:
            from app.modules.article.models import Article, ArticleStatus, ArticleTag
            has_articles_filter = Tag.id.in_(
                select(ArticleTag.tag_id)
                .join(Article, Article.id == ArticleTag.article_id)
                .where(
                    Article.deleted_at.is_(None),
                    Article.is_draft.is_(False),
                    Article.status == ArticleStatus.PUBLISHED
                )
            )
            count_stmt = count_stmt.where(has_articles_filter)
            data_stmt = data_stmt.where(has_articles_filter)

        # Đếm tổng
        count_result = await db.execute(count_stmt)
        total = count_result.scalar() or 0

        # Phân trang và sắp xếp
        data_stmt = data_stmt.order_by(Tag.sort_order.asc(), desc(Tag.created_at)).offset(skip).limit(limit)
        data_result = await db.execute(data_stmt)
        items = list(data_result.scalars().all())

        # Tính toán article_count cho mỗi tag (chỉ đếm bài viết công khai)
        if items:
            from app.modules.article.models import Article, ArticleStatus, ArticleTag
            tag_ids = [t.id for t in items]
            counts_query = (
                select(ArticleTag.tag_id, func.count(ArticleTag.article_id))
                .join(Article, Article.id == ArticleTag.article_id)
                .where(
                    ArticleTag.tag_id.in_(tag_ids),
                    Article.deleted_at.is_(None),
                    Article.is_draft.is_(False),
                    Article.status == ArticleStatus.PUBLISHED
                )
                .group_by(ArticleTag.tag_id)
            )
            counts_res = await db.execute(counts_query)
            counts_map = {row[0]: row[1] for row in counts_res.all() if row[0] is not None}
            for tag in items:
                tag.article_count = counts_map.get(tag.id, 0)
        else:
            for tag in items:
                tag.article_count = 0

        return items, total

    async def get_tag_by_id(self, db: AsyncSession, tag_id: uuid.UUID) -> Tag:
        """
        Lấy chi tiết Tag theo ID. Raise NotFoundException nếu không tìm thấy hoặc đã bị xóa mềm.
        """
        stmt = select(Tag).where(Tag.id == tag_id, Tag.deleted_at == None)
        result = await db.execute(stmt)
        tag = result.scalar_one_or_none()

        if not tag:
            raise NotFoundException(
                message="Không tìm thấy Tag hoặc Tag đã bị xóa",
                error_code="TAG_NOT_FOUND",
                details={"tag_id": str(tag_id)},
            )

        # Tính toán article_count cho tag này
        from app.modules.article.models import Article, ArticleStatus, ArticleTag
        count_query = (
            select(func.count(ArticleTag.article_id))
            .join(Article, Article.id == ArticleTag.article_id)
            .where(
                ArticleTag.tag_id == tag_id,
                Article.deleted_at == None,
                Article.is_draft == False,
                Article.status == ArticleStatus.PUBLISHED
            )
        )
        count_res = await db.execute(count_query)
        tag.article_count = count_res.scalar() or 0

        return tag

    async def create_tag(self, db: AsyncSession, data: TagCreate) -> Tag:
        """
        Tạo Tag mới. Kiểm tra trùng tên và tự sinh slug unique.
        """
        # Kiểm tra trùng tên (không tính các record đã bị xóa mềm)
        stmt = select(Tag).where(Tag.name == data.name, Tag.deleted_at == None)
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise ConflictException(
                message=f"Tag với tên '{data.name}' đã tồn tại",
                error_code="TAG_NAME_EXISTS",
                details={"name": data.name},
            )

        # Tính toán slug unique
        if data.slug:
            slug = data.slug
            # Validate slug đã cung cấp có bị trùng không
            slug_stmt = select(Tag).where(Tag.slug == slug, Tag.deleted_at == None)
            slug_res = await db.execute(slug_stmt)
            if slug_res.scalar_one_or_none():
                # Nếu slug người dùng cung cấp bị trùng, tự động resolve để tạo slug mới unique
                slug = await self._resolve_unique_slug(db, slug)
        else:
            slug = await self._resolve_unique_slug(db, data.name)

        tag = Tag(
            name=data.name,
            slug=slug,
            description=data.description,
            color=data.color,
            sort_order=data.sort_order,
            is_active=data.is_active,
        )
        db.add(tag)
        await db.flush()
        logger.info(f"Created Tag: {tag.name} (slug={tag.slug}, id={tag.id})")
        return tag

    async def update_tag(self, db: AsyncSession, tag_id: uuid.UUID, data: TagUpdate) -> Tag:
        """
        Cập nhật Tag. Kiểm tra trùng tên và tự sinh slug unique nếu tên thay đổi.
        """
        tag = await self.get_tag_by_id(db, tag_id)
        update_data = data.model_dump(exclude_unset=True)

        if "name" in update_data and update_data["name"] != tag.name:
            # Check trùng name
            name_stmt = select(Tag).where(
                Tag.name == update_data["name"],
                Tag.id != tag_id,
                Tag.deleted_at == None
            )
            name_res = await db.execute(name_stmt)
            if name_res.scalar_one_or_none():
                raise ConflictException(
                    message=f"Tag với tên '{update_data['name']}' đã tồn tại",
                    error_code="TAG_NAME_EXISTS",
                    details={"name": update_data["name"]},
                )

            # Nếu đổi name và không truyền slug mới -> tự động sinh slug mới
            if "slug" not in update_data:
                update_data["slug"] = await self._resolve_unique_slug(db, update_data["name"], current_id=tag_id)

        if "slug" in update_data and update_data["slug"] != tag.slug:
            # Check trùng slug
            update_data["slug"] = await self._resolve_unique_slug(db, update_data["slug"], current_id=tag_id)

        # Cập nhật các trường
        for field, value in update_data.items():
            setattr(tag, field, value)

        db.add(tag)
        await db.flush()
        logger.info(f"Updated Tag: {tag.name} (slug={tag.slug}, id={tag_id})")
        return tag

    async def delete_tag(self, db: AsyncSession, tag_id: uuid.UUID) -> None:
        """
        Xóa mềm Tag bằng cách gán deleted_at.
        """
        tag = await self.get_tag_by_id(db, tag_id)
        tag.deleted_at = datetime.now(timezone.utc)
        db.add(tag)
        await db.flush()
        logger.info(f"Soft deleted Tag: {tag.name} (id={tag_id})")

    async def toggle_tag_status(self, db: AsyncSession, tag_id: uuid.UUID, is_active: bool) -> Tag:
        """
        Bật/Tắt trạng thái hoạt động của Tag.
        """
        tag = await self.get_tag_by_id(db, tag_id)
        tag.is_active = is_active
        db.add(tag)
        await db.flush()
        logger.info(f"Toggled Tag status: {tag.name} (is_active={is_active}, id={tag_id})")
        return tag

    async def _resolve_unique_slug(
        self, db: AsyncSession, base_text: str, current_id: Optional[uuid.UUID] = None
    ) -> str:
        """
        Tạo slug duy nhất toàn bảng. Nếu bị trùng sẽ tự động thêm hậu tố -1, -2...
        """
        base_slug = generate_slug(base_text)
        if not base_slug:
            base_slug = "tag"

        slug_candidate = base_slug
        counter = 1

        while True:
            # Check trùng slug
            query = select(Tag.id).where(Tag.slug == slug_candidate, Tag.deleted_at == None)
            if current_id:
                query = query.where(Tag.id != current_id)

            result = await db.execute(query)
            exists = result.scalar_one_or_none()

            if not exists:
                break

            slug_candidate = f"{base_slug}-{counter}"
            counter += 1

        return slug_candidate


tag_service = TagService()
