import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple

from loguru import logger
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictException, NotFoundException
from app.modules.category.utils import generate_slug
from app.modules.tag.models import Tag
from app.modules.tag.schemas import TagCreate, TagUpdate


class TagService:
    """
    Business logic cho quản lý Tag dùng chung.
    """

    def _apply_translation(self, tag: Tag, lang: str = "vi") -> Tag:
        """
        Đọc bản dịch của ngôn ngữ chỉ định (hoặc fallback tiếng Việt) từ translations
        và gán vào các thuộc tính phẳng của Tag. Nếu không có bản dịch nào, fallback về cột legacy.
        """
        if not tag:
            return tag

        # 1. Tìm bản dịch của ngôn ngữ đích (lang)
        target_translation = None
        for t in getattr(tag, "translations", []):
            if t.language and t.language.code == lang:
                target_translation = t
                break

        # 2. Nếu không tìm thấy hoặc tên rỗng, fallback về tiếng Việt ("vi")
        if (not target_translation or not target_translation.name) and lang != "vi":
            for t in getattr(tag, "translations", []):
                if t.language and t.language.code == "vi":
                    target_translation = t
                    break

        # 3. Gán thuộc tính hoặc fallback về mặc định
        if target_translation:
            tag.name = target_translation.name
            tag.slug = target_translation.slug
            tag.description = target_translation.description
        else:
            tag.name = "Chưa dịch"
            tag.slug = f"chua-dich-{tag.id}"
            tag.description = ""

        return tag

    async def list_tags(
        self,
        db: AsyncSession,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        only_has_articles: bool = False,
        page: int = 1,
        limit: int = 10,
        lang: str = "vi"
    ) -> Tuple[list[Tag], int]:
        """
        Lấy danh sách các Tag chưa bị xóa mềm với phân trang, tìm kiếm và lọc tag có bài viết.
        """
        skip = (page - 1) * limit
        from app.modules.tag.models import TagTranslation
        from app.modules.language.models import Language

        # Query đếm tổng số phần tử thỏa mãn điều kiện
        count_stmt = select(func.count(Tag.id)).where(Tag.deleted_at.is_(None))
        
        # Query lấy dữ liệu
        data_stmt = select(Tag).where(Tag.deleted_at.is_(None)).options(
            selectinload(Tag.translations).selectinload(TagTranslation.language)
        )

        if search:
            # Tìm kiếm theo bản dịch tiếng Việt
            search_filter = Tag.translations.any(
                (TagTranslation.name.ilike(f"%{search}%")) |
                (TagTranslation.description.ilike(f"%{search}%"))
            )
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
                self._apply_translation(tag, lang=lang)
        else:
            for tag in items:
                tag.article_count = 0

        return items, total

    async def get_tag_by_id(self, db: AsyncSession, tag_id: uuid.UUID, lang: str = "vi") -> Tag:
        """
        Lấy chi tiết Tag theo ID. Raise NotFoundException nếu không tìm thấy hoặc đã bị xóa mềm.
        """
        from app.modules.tag.models import TagTranslation
        stmt = select(Tag).where(Tag.id == tag_id, Tag.deleted_at == None).options(
            selectinload(Tag.translations).selectinload(TagTranslation.language)
        )
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
        self._apply_translation(tag, lang=lang)

        return tag

    async def create_tag(self, db: AsyncSession, data: TagCreate) -> Tag:
        """
        Tạo Tag mới. Đa ngôn ngữ hóa, lưu cả bản dịch và legacy fields.
        """
        # 1. Tạo Tag object chính
        tag = Tag(
            color=data.color,
            sort_order=data.sort_order,
            is_active=data.is_active,
        )

        db.add(tag)
        await db.flush()

        # 2. Tạo các bản dịch
        from app.modules.language.models import Language
        from app.modules.tag.models import TagTranslation
        for lang_code, trans_item in data.translations.items():
            lang_query = select(Language.id).where(Language.code == lang_code)
            lang_res = await db.execute(lang_query)
            lang_id = lang_res.scalar()
            if not lang_id:
                continue

            slug = trans_item.slug or generate_slug(trans_item.name)
            slug = await self._resolve_unique_slug(db, slug, lang_id)

            translation = TagTranslation(
                tag_id=tag.id,
                language_id=lang_id,
                name=trans_item.name,
                slug=slug,
                description=trans_item.description
            )
            db.add(translation)

        await db.flush()
        db.expire(tag, ["translations"])
        logger.info(f"Created Tag: id={tag.id}")
        
        # Load lại translations để schema serializer hoạt động đúng
        stmt = select(Tag).where(Tag.id == tag.id).options(
            selectinload(Tag.translations).selectinload(TagTranslation.language)
        )
        res = await db.execute(stmt)
        return res.scalar()

    async def update_tag(self, db: AsyncSession, tag_id: uuid.UUID, data: TagUpdate) -> Tag:
        """
        Cập nhật Tag và các bản dịch.
        """
        tag = await self.get_tag_by_id(db, tag_id)

        if data.color is not None:
            tag.color = data.color
        if data.sort_order is not None:
            tag.sort_order = data.sort_order
        if data.is_active is not None:
            tag.is_active = data.is_active

        # Cập nhật translations
        from app.modules.tag.models import TagTranslation
        from app.modules.language.models import Language
        
        if data.translations is not None:
            for lang_code, trans_item in data.translations.items():
                lang_query = select(Language.id).where(Language.code == lang_code)
                lang_res = await db.execute(lang_query)
                lang_id = lang_res.scalar()
                if not lang_id:
                    continue

                stmt = select(TagTranslation).where(
                    TagTranslation.tag_id == tag_id,
                    TagTranslation.language_id == lang_id
                )
                trans_res = await db.execute(stmt)
                translation = trans_res.scalar_one_or_none()

                slug = trans_item.slug or generate_slug(trans_item.name)
                slug = await self._resolve_unique_slug(db, slug, lang_id, current_tag_id=tag_id)

                if translation:
                    translation.name = trans_item.name
                    translation.slug = slug
                    translation.description = trans_item.description
                else:
                    translation = TagTranslation(
                        tag_id=tag_id,
                        language_id=lang_id,
                        name=trans_item.name,
                        slug=slug,
                        description=trans_item.description
                    )
                db.add(translation)

        db.add(tag)
        await db.flush()
        db.expire(tag, ["translations"])
        logger.info(f"Updated Tag: id={tag_id}")

        # Load lại translations đầy đủ
        stmt = select(Tag).where(Tag.id == tag.id).options(
            selectinload(Tag.translations).selectinload(TagTranslation.language)
        )
        res = await db.execute(stmt)
        return res.scalar()

    async def delete_tag(self, db: AsyncSession, tag_id: uuid.UUID) -> None:
        """
        Xóa mềm Tag bằng cách gán deleted_at.
        """
        tag = await self.get_tag_by_id(db, tag_id)
        tag.deleted_at = datetime.now(timezone.utc)
        db.add(tag)
        await db.flush()
        logger.info(f"Soft deleted Tag: id={tag_id}")

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
        self, db: AsyncSession, base_text: str, language_id: uuid.UUID, current_tag_id: Optional[uuid.UUID] = None
    ) -> str:
        """Tính toán slug không trùng lặp trong bảng TagTranslation theo từng ngôn ngữ."""
        base_slug = generate_slug(base_text)
        if not base_slug:
            base_slug = "tag"

        slug_candidate = base_slug

        from app.modules.tag.models import TagTranslation
        query = select(TagTranslation.slug).where(
            TagTranslation.language_id == language_id,
            TagTranslation.slug == slug_candidate
        )
        if current_tag_id:
            query = query.where(TagTranslation.tag_id != current_tag_id)

        res = await db.execute(query)
        exists = res.scalar_one_or_none()

        if exists:
            import uuid as py_uuid
            suffix = str(py_uuid.uuid4())[:8]
            slug_candidate = f"{base_slug}-{suffix}"

        return slug_candidate

    async def check_slug_uniqueness(
        self, db: AsyncSession, slug: str, lang_code: str = "vi", exclude_id: Optional[uuid.UUID] = None
    ) -> dict:
        """Kiểm tra xem slug của Tag có trùng lặp không và trả về đề xuất slug mới không trùng."""
        from app.modules.language.models import Language
        # Lấy language_id từ code
        q = select(Language.id).where(Language.code == lang_code)
        res = await db.execute(q)
        lang_id = res.scalar_one_or_none()
        if not lang_id:
            # Fallback lấy vi
            q_vi = select(Language.id).where(Language.code == "vi")
            res_vi = await db.execute(q_vi)
            lang_id = res_vi.scalar_one_or_none()

        suggested = await self._resolve_unique_slug(db, slug, lang_id, current_tag_id=exclude_id)
        exists = (suggested != slug)
        return {
            "exists": exists,
            "suggested_slug": suggested
        }


tag_service = TagService()
