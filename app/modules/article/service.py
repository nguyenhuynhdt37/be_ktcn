import uuid
import re
import math
from datetime import datetime, timezone
from typing import Any, Optional, Tuple

def slugify(text: str) -> str:
    """
    Chuyển đổi văn bản tiếng Việt có dấu sang không dấu và chuẩn hóa dạng slug.
    """
    text = text.lower()
    text = text.replace('_', '-')
    patterns = {
        '[àáảãạăằắẳẵặâầấẩẫậ]': 'a',
        '[èéẻẽẹêềếểễệ]': 'e',
        '[ìíỉĩị]': 'i',
        '[òóỏõọôồốổỗộơờớởỡợ]': 'o',
        '[ùúủũụưừứửữự]': 'u',
        '[ỳýỷỹỵ]': 'y',
        'đ': 'd'
    }
    for pattern, replacement in patterns.items():
        text = re.sub(pattern, replacement, text)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text)
    return text.strip('-')

from loguru import logger
from sqlalchemy import select, func, desc, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload, load_only

from app.core.exceptions import BadRequestException, NotFoundException, ForbiddenException
from app.modules.article.models import Article, ArticleStatus, ArticleTranslation
from app.modules.article.schemas import (
    BulkActionEnum, BulkActionResponse, ArticleStatsResponse, 
    ArticleAttributesUpdateRequest, ArticleCreateRequest, SlugCheckResponse, 
    ArticleDraftsCountResponse, ArticleUpdateRequest
)
from app.modules.auth.models import User
from app.modules.category.models import Category
from app.modules.tag.models import Tag
from app.modules.article.repositories.query_builder import ArticleQueryBuilder, ArticleFilterParams, SortStrategy


class ArticleService:
    """
    Business logic phục vụ cho module Articles.
    """

    def _apply_translation(self, article: Article, lang: str = "vi") -> Article:
        """
        Đọc bản dịch của ngôn ngữ chỉ định (hoặc fallback tiếng Việt) từ translations
        và gán vào các thuộc tính phẳng của Article. Nếu không có bản dịch nào, fallback về cột legacy.
        """
        if not article:
            return article
        
        # 1. Tìm bản dịch của ngôn ngữ đích
        target_translation = None
        for t in getattr(article, "translations", []):
            if t.language and t.language.code == lang:
                target_translation = t
                break
                
        # 2. Nếu không tìm thấy hoặc title rỗng, fallback về tiếng Việt ("vi")
        if (not target_translation or not target_translation.title) and lang != "vi":
            for t in getattr(article, "translations", []):
                if t.language and t.language.code == "vi":
                    target_translation = t
                    break
                    
        # 3. Gán thuộc tính hoặc fallback về mặc định
        if target_translation:
            article.title = target_translation.title
            article.slug = target_translation.slug
            article.excerpt = target_translation.excerpt
            article.content = target_translation.content
            article.seo_title = target_translation.seo_title
            article.seo_description = target_translation.seo_description
            article.canonical_url = target_translation.canonical_url
            article.robots = target_translation.robots
            article.og_title = target_translation.og_title
            article.og_description = target_translation.og_description
            article.og_image = target_translation.og_image
        else:
            article.title = "Chưa dịch"
            article.slug = f"chua-dich-{article.id}"
            article.excerpt = None
            article.content = ""
            article.seo_title = None
            article.seo_description = None
            article.canonical_url = None
            article.robots = "index, follow"
            article.og_title = None
            article.og_description = None
            article.og_image = None
            
        return article

    async def _resolve_unique_slug(
        self, db: AsyncSession, base_text: str, language_id: uuid.UUID, exclude_article_id: Optional[uuid.UUID] = None
    ) -> str:
        """Tính toán slug không trùng lặp trong bảng ArticleTranslation theo từng ngôn ngữ."""
        base_slug = slugify(base_text)
        if not base_slug:
            base_slug = "bai-viet"
            
        slug_candidate = base_slug
        
        from app.modules.article.models import ArticleTranslation
        query = select(ArticleTranslation.slug).where(
            ArticleTranslation.language_id == language_id,
            ArticleTranslation.slug == slug_candidate
        )
        if exclude_article_id:
            query = query.where(ArticleTranslation.article_id != exclude_article_id)
            
        res = await db.execute(query)
        exists = res.scalar_one_or_none()
        
        if exists:
            # Sinh slug mới bằng cách thêm uuid rút gọn 8 ký tự
            import uuid as py_uuid
            suffix = str(py_uuid.uuid4())[:8]
            slug_candidate = f"{base_slug}-{suffix}"
            
        return slug_candidate

    async def list_articles(
        self,
        db: AsyncSession,
        *,
        page: int = 1,
        page_size: int = 10,
        search: Optional[str] = None,
        category_id: Optional[uuid.UUID] = None,
        category_slugs: Optional[list[str]] = None,
        exclude_category_slugs: Optional[list[str]] = None,
        author_id: Optional[uuid.UUID] = None,
        tag_ids: Optional[list[uuid.UUID]] = None,
        status: Optional[ArticleStatus] = None,
        is_pinned: Optional[bool] = None,
        is_draft: Optional[bool] = False,
        created_from: Optional[datetime] = None,
        created_to: Optional[datetime] = None,
        published_from: Optional[datetime] = None,
        published_to: Optional[datetime] = None,
        deleted: bool = False,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
        lang: str = "vi",
    ) -> Tuple[list[Article], int]:
        """
        Query danh sách bài viết từ database với phân trang, lọc và sắp xếp động tối ưu (Admin CMS).
        """
        builder = ArticleQueryBuilder(db)

        # Lấy language_id cho resolved_translation
        from app.modules.language.models import Language
        lang_res = await db.execute(select(Language.id).where(Language.code == lang))
        lang_id = lang_res.scalar()
        if not lang_id:
            lang_res = await db.execute(select(Language.id).where(Language.code == "vi"))
            lang_id = lang_res.scalar()

        if lang_id:
            builder.resolve_translation(lang_id)
        
        # Áp dụng Admin scope và eager load quan hệ
        builder.admin_scope(deleted=deleted)
        builder.with_portal_relations()
        
        # Đóng gói filter params
        filter_params = ArticleFilterParams(
            category_id=category_id,
            category_slugs=category_slugs,
            exclude_category_slugs=exclude_category_slugs,
            author_id=author_id,
            tag_ids=tag_ids,
            is_pinned=is_pinned,
            published_from=published_from,
            published_to=published_to,
            status=status
        )
        builder.filter(filter_params)
        
        # Bổ sung các bộ lọc đặc thù chỉ Admin mới có
        if is_draft is not None:
            builder.query = builder.query.where(Article.is_draft == is_draft)
            
        if created_from:
            builder.query = builder.query.where(Article.created_at >= created_from)
        if created_to:
            builder.query = builder.query.where(Article.created_at <= created_to)
            
        # Tìm kiếm Generic
        if search:
            builder.search(
                fields=[ArticleTranslation.title, ArticleTranslation.slug],
                keyword=search
            )
            
        # Đếm tổng
        total = await builder.get_total_count()
        
        # Sắp xếp và phân trang
        builder.sort(
            strategy=SortStrategy.CUSTOM,
            sort_by=sort_by,
            sort_dir=sort_dir
        )
        builder.paginate(page=page, page_size=page_size)
        
        # Thực thi
        items = await builder.execute()
        for item in items:
            self._apply_translation(item, lang=lang)
            if item.category:
                from app.modules.category.service import category_service
                category_service._apply_translation(item.category, lang=lang)
            for tag in item.tags:
                from app.modules.tag.service import tag_service
                tag_service._apply_translation(tag, lang=lang)
        return items, total

    async def archive_article(
        self,
        db: AsyncSession,
        *,
        article_id: uuid.UUID,
        current_user: Any,
    ) -> Article:
        """
        Chuyển đổi trạng thái của bài viết từ PUBLISHED sang ARCHIVED.
        Không cho phép thực hiện đối với các trạng thái khác (như DRAFT, SCHEDULED).
        """
        # Query bài viết kèm các quan hệ cần hiển thị ở response
        from app.modules.category.models import CategoryTranslation
        from app.modules.tag.models import TagTranslation
        from app.modules.article.models import ArticleTranslation

        stmt = (
            select(Article)
            .where(Article.id == article_id, Article.deleted_at == None)
            .options(
                joinedload(Article.category).options(
                    selectinload(Category.translations).selectinload(CategoryTranslation.language)
                ),
                joinedload(Article.author).joinedload(User.avatar),
                joinedload(Article.author).load_only(User.id, User.username, User.full_name, User.avatar_url),
                selectinload(Article.tags).options(
                    selectinload(Tag.translations).selectinload(TagTranslation.language)
                ),
                selectinload(Article.translations).selectinload(ArticleTranslation.language)
            )
        )
        result = await db.execute(stmt)
        article = result.scalars().first()
        
        if not article:
            raise NotFoundException(message="Không tìm thấy bài viết hoặc bài viết đã bị xóa.")

        # Idempotent: Nếu đã là ARCHIVED rồi thì không cần làm gì, trả về luôn
        if article.status == ArticleStatus.ARCHIVED:
            return article

        # Nghiệp vụ: Chỉ cho phép chuyển sang lưu trữ từ trạng thái PUBLISHED
        if article.status != ArticleStatus.PUBLISHED:
            raise BadRequestException(
                message=f"Chỉ cho phép lưu trữ bài viết đang ở trạng thái PUBLISHED. Trạng thái hiện tại: {article.status.value}"
            )

        # Cập nhật trạng thái
        article.status = ArticleStatus.ARCHIVED
        article.last_edited_at = datetime.now(timezone.utc)
        db.add(article)

        # Ghi nhận audit log
        from app.modules.audit.service import log_action
        log_title = "Chưa dịch"
        for t in getattr(article, "translations", []):
            if t.language and t.language.code == "vi":
                log_title = t.title
                break
        await log_action(
            db,
            current_user,
            "ARTICLE_ARCHIVED",
            "article",
            article.id,
            {"title": log_title, "previous_status": "PUBLISHED"}
        )

        await db.commit()
        return article

    async def publish_article(
        self,
        db: AsyncSession,
        *,
        article_id: uuid.UUID,
        current_user: Any,
    ) -> Article:
        """
        Khôi phục bài viết từ trạng thái ARCHIVED (Lưu trữ) quay trở lại PUBLISHED (Công khai).
        Không cho phép thực hiện đối với các trạng thái khác (như DRAFT, SCHEDULED).
        """
        # Query bài viết kèm các quan hệ cần hiển thị ở response
        from app.modules.category.models import CategoryTranslation
        from app.modules.tag.models import TagTranslation
        from app.modules.article.models import ArticleTranslation

        stmt = (
            select(Article)
            .where(Article.id == article_id, Article.deleted_at == None)
            .options(
                joinedload(Article.category).options(
                    selectinload(Category.translations).selectinload(CategoryTranslation.language)
                ),
                joinedload(Article.author).joinedload(User.avatar),
                joinedload(Article.author).load_only(User.id, User.username, User.full_name, User.avatar_url),
                selectinload(Article.tags).options(
                    selectinload(Tag.translations).selectinload(TagTranslation.language)
                ),
                selectinload(Article.translations).selectinload(ArticleTranslation.language)
            )
        )
        result = await db.execute(stmt)
        article = result.scalars().first()
        
        if not article:
            raise NotFoundException(message="Không tìm thấy bài viết hoặc bài viết đã bị xóa.")

        # Idempotent: Nếu đã là PUBLISHED rồi thì không cần làm gì, trả về luôn
        if article.status == ArticleStatus.PUBLISHED:
            return article

        # Nghiệp vụ: Chỉ cho phép chuyển sang công khai từ trạng thái ARCHIVED
        if article.status != ArticleStatus.ARCHIVED:
            raise BadRequestException(
                message=f"Chỉ cho phép khôi phục bài viết đang ở trạng thái ARCHIVED sang công khai. Trạng thái hiện tại: {article.status.value}"
            )

        # Cập nhật trạng thái
        article.status = ArticleStatus.PUBLISHED
        article.published_at = article.published_at or datetime.now(timezone.utc)
        article.last_edited_at = datetime.now(timezone.utc)
        db.add(article)

        # Ghi nhận audit log
        from app.modules.audit.service import log_action
        log_title = "Chưa dịch"
        for t in getattr(article, "translations", []):
            if t.language and t.language.code == "vi":
                log_title = t.title
                break
        await log_action(
            db,
            current_user,
            "ARTICLE_PUBLISHED",
            "article",
            article.id,
            {"title": log_title, "previous_status": "ARCHIVED"}
        )

        await db.commit()
        return article

    async def bulk_update_status(
        self,
        db: AsyncSession,
        *,
        article_ids: list[uuid.UUID],
        action: BulkActionEnum,
        current_user: Any,
    ) -> BulkActionResponse:
        """
        Cập nhật trạng thái hàng loạt cho danh sách bài viết.
        Hỗ trợ: archive, publish, delete, restore.
        """
        # Nếu restore, query cả những bài đã bị xóa mềm (deleted_at != None)
        if action == BulkActionEnum.RESTORE:
            stmt = select(Article).where(Article.id.in_(article_ids))
        else:
            stmt = select(Article).where(Article.id.in_(article_ids), Article.deleted_at == None)
        
        result = await db.execute(stmt)
        articles = {art.id: art for art in result.scalars().all()}
        
        success_count = 0
        failed_count = 0
        failed_ids = []
        
        from app.modules.audit.service import log_action
        
        for art_id in article_ids:
            article = articles.get(art_id)
            if not article:
                failed_count += 1
                failed_ids.append(art_id)
                continue
            
            # Phân quyền: Chỉ chủ sở hữu bài viết mới được thực hiện bulk action lên bài viết đó
            if article.author_id != current_user.id:
                failed_count += 1
                failed_ids.append(art_id)
                continue
            
            try:
                if action == BulkActionEnum.ARCHIVE:
                    # Chỉ được archive bài viết đang PUBLISHED
                    if article.status != ArticleStatus.PUBLISHED:
                        raise ValueError("Chỉ bài viết PUBLISHED mới có thể archive")
                    
                    previous_status = article.status.value
                    article.status = ArticleStatus.ARCHIVED
                    article.last_edited_at = datetime.now(timezone.utc)
                    db.add(article)
                    
                    await log_action(
                        db, current_user, "ARTICLE_ARCHIVED", "article", article.id,
                        {"title": article.title, "previous_status": previous_status, "bulk": True}
                    )
                    
                elif action == BulkActionEnum.PUBLISH:
                    # Chỉ được publish bài viết đang ARCHIVED
                    if article.status != ArticleStatus.ARCHIVED:
                        raise ValueError("Chỉ bài viết ARCHIVED mới có thể publish")
                    
                    previous_status = article.status.value
                    article.status = ArticleStatus.PUBLISHED
                    article.published_at = article.published_at or datetime.now(timezone.utc)
                    article.last_edited_at = datetime.now(timezone.utc)
                    db.add(article)
                    
                    await log_action(
                        db, current_user, "ARTICLE_PUBLISHED", "article", article.id,
                        {"title": article.title, "previous_status": previous_status, "bulk": True}
                    )
                    
                elif action == BulkActionEnum.DELETE:
                    # Xóa mềm bài viết
                    article.deleted_at = datetime.now(timezone.utc)
                    db.add(article)
                    
                    await log_action(
                        db, current_user, "ARTICLE_DELETED", "article", article.id,
                        {"title": article.title, "bulk": True}
                    )
                    
                elif action == BulkActionEnum.RESTORE:
                    # Khôi phục bài viết đã xóa mềm
                    if article.deleted_at is None:
                        raise ValueError("Bài viết chưa bị xóa")
                    
                    article.deleted_at = None
                    db.add(article)
                    
                    await log_action(
                        db, current_user, "ARTICLE_RESTORED", "article", article.id,
                        {"title": article.title, "bulk": True}
                    )
                
                success_count += 1
            except Exception:
                failed_count += 1
                failed_ids.append(art_id)
                
        await db.commit()
        
        action_verbs = {
            BulkActionEnum.ARCHIVE: "lưu trữ",
            BulkActionEnum.PUBLISH: "công khai",
            BulkActionEnum.DELETE: "xóa tạm",
            BulkActionEnum.RESTORE: "khôi phục"
        }
        verb = action_verbs.get(action, "cập nhật")
        message = f"Đã thực hiện {verb} hàng loạt bài viết. Thành công: {success_count}, Thất bại: {failed_count}."
        
        return BulkActionResponse(
            success_count=success_count,
            failed_count=failed_count,
            failed_ids=failed_ids,
            message=message
        )

    async def get_article_stats(self, db: AsyncSession) -> ArticleStatsResponse:
        """
        Lấy thống kê nhanh số lượng bài viết và số lượt xem trong tháng.
        """
        # 1. Đếm bài viết theo các trạng thái (chưa xóa mềm)
        stmt_statuses = (
            select(Article.status, func.count(Article.id))
            .where(Article.deleted_at == None)
            .group_by(Article.status)
        )
        res_statuses = await db.execute(stmt_statuses)
        status_counts = {status: count for status, count in res_statuses.all()}
        
        # 2. Đếm số lượng trong thùng rác (đã xóa mềm)
        stmt_trash = select(func.count(Article.id)).where(Article.deleted_at != None)
        res_trash = await db.execute(stmt_trash)
        trash_count = res_trash.scalar() or 0
        
        # 3. Tính tổng lượt xem của các bài viết được xuất bản trong tháng hiện tại
        now = datetime.now(timezone.utc)
        start_of_month = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        
        stmt_views = (
            select(func.sum(Article.view_count))
            .where(Article.deleted_at == None, Article.published_at >= start_of_month)
        )
        res_views = await db.execute(stmt_views)
        total_views = res_views.scalar() or 0
        
        return ArticleStatsResponse(
            published_count=status_counts.get(ArticleStatus.PUBLISHED, 0),
            scheduled_count=status_counts.get(ArticleStatus.SCHEDULED, 0),
            draft_count=status_counts.get(ArticleStatus.DRAFT, 0),
            archived_count=status_counts.get(ArticleStatus.ARCHIVED, 0),
            trash_count=trash_count,
            total_views_this_month=total_views
        )

    async def update_article_attributes(
        self,
        db: AsyncSession,
        *,
        article_id: uuid.UUID,
        payload: ArticleAttributesUpdateRequest,
        current_user: Any,
    ) -> Article:
        """
        Cập nhật nhanh các thuộc tính đặc biệt (is_pinned) của bài viết.
        """
        from app.modules.category.models import CategoryTranslation
        from app.modules.tag.models import TagTranslation
        from app.modules.article.models import ArticleTranslation

        stmt = (
            select(Article)
            .where(Article.id == article_id, Article.deleted_at == None)
            .options(
                joinedload(Article.category).options(
                    selectinload(Category.translations).selectinload(CategoryTranslation.language)
                ),
                joinedload(Article.author).joinedload(User.avatar),
                joinedload(Article.author).load_only(User.id, User.username, User.full_name, User.avatar_url),
                selectinload(Article.tags).options(
                    selectinload(Tag.translations).selectinload(TagTranslation.language)
                ),
                selectinload(Article.translations).selectinload(ArticleTranslation.language)
            )
        )
        result = await db.execute(stmt)
        article = result.scalars().first()
        
        if not article:
            raise NotFoundException(message="Không tìm thấy bài viết hoặc bài viết đã bị xóa.")

        changes = {}
        if payload.is_pinned is not None:
            changes["is_pinned"] = {"old": article.is_pinned, "new": payload.is_pinned}
            article.is_pinned = payload.is_pinned

        if changes:
            article.last_edited_at = datetime.now(timezone.utc)
            db.add(article)
            
            # Ghi nhận audit log
            from app.modules.audit.service import log_action
            log_title = "Chưa dịch"
            for t in getattr(article, "translations", []):
                if t.language and t.language.code == "vi":
                    log_title = t.title
                    break
            await log_action(
                db,
                current_user,
                "ARTICLE_UPDATED",
                "article",
                article.id,
                {"title": log_title, "attribute_changes": changes}
            )
            await db.commit()
            
        return article

    async def create_article(
        self,
        db: AsyncSession,
        payload: ArticleCreateRequest,
        current_user: Any
    ) -> Article:
        """
        Tạo bài viết mới hỗ trợ đa ngôn ngữ.
        """
        # Tự động trích xuất category_id từ object category nếu category_id là None
        category_id = payload.category_id
        if not category_id and payload.category and isinstance(payload.category, dict):
            try:
                category_id = uuid.UUID(str(payload.category.get("id")))
            except (ValueError, TypeError):
                pass

        # Tự động trích xuất tag_ids từ list tags nếu tag_ids trống
        tag_ids = list(payload.tag_ids) if payload.tag_ids else []
        if not tag_ids and payload.tags and isinstance(payload.tags, list):
            for t in payload.tags:
                if isinstance(t, dict) and t.get("id"):
                    try:
                        tag_ids.append(uuid.UUID(str(t.get("id"))))
                    except (ValueError, TypeError):
                        pass

        # 1. Kiểm tra Category & Content theo trạng thái xuất bản
        vi_trans = payload.translations.get("vi")
        ref_trans = vi_trans or (list(payload.translations.values())[0] if payload.translations else None)

        if not payload.is_draft:
            if not category_id:
                raise BadRequestException(message="Danh mục là bắt buộc khi xuất bản hoặc lên lịch bài viết.")
            if not ref_trans or not ref_trans.content or not ref_trans.content.strip():
                raise BadRequestException(message="Nội dung bài viết không được để trống khi xuất bản hoặc lên lịch.")

        if category_id:
            cat_stmt = select(Category).where(Category.id == category_id, Category.deleted_at == None)
            cat_res = await db.execute(cat_stmt)
            category = cat_res.scalars().first()
            if not category:
                raise BadRequestException(message="Danh mục không tồn tại hoặc đã bị xóa.")

        if payload.department_id:
            from app.modules.department.models import Department
            if not (await db.execute(select(Department.id).where(Department.id == payload.department_id, Department.deleted_at.is_(None)))).scalar():
                raise BadRequestException(message="Đơn vị liên quan không tồn tại hoặc đã bị xóa.")
        if payload.program_id:
            from app.modules.program.models import Program
            program = (await db.execute(select(Program).where(Program.id == payload.program_id, Program.deleted_at.is_(None)))).scalar_one_or_none()
            if not program:
                raise BadRequestException(message="Chương trình đào tạo không tồn tại hoặc đã bị xóa.")
            if payload.department_id and program.department_id != payload.department_id:
                raise BadRequestException(message="Chương trình đào tạo không thuộc đơn vị đã chọn.")

        # 2. Kiểm tra Tags nếu có truyền
        tags_list = []
        if tag_ids:
            tags_stmt = select(Tag).where(Tag.id.in_(tag_ids), Tag.deleted_at == None)
            tags_res = await db.execute(tags_stmt)
            tags_list = list(tags_res.scalars().all())
            if len(tags_list) != len(tag_ids):
                raise BadRequestException(message="Một hoặc nhiều thẻ tag không tồn tại hoặc đã bị xóa.")

        # 3. Kiểm tra validation khi lên lịch SCHEDULED
        now = datetime.now(timezone.utc)
        if payload.status == ArticleStatus.SCHEDULED and not payload.is_draft:
            if not payload.publish_at:
                raise BadRequestException(message="Yêu cầu truyền thời gian xuất bản (publish_at) khi lên lịch.")
            if payload.publish_at <= now:
                raise BadRequestException(message="Thời gian lên lịch xuất bản (publish_at) phải ở trong tương lai.")
        
        # 4. Kiểm tra expire_at
        if payload.expire_at and payload.publish_at and payload.expire_at <= payload.publish_at:
            raise BadRequestException(message="Thời điểm hết hạn hiển thị (expire_at) phải lớn hơn thời điểm xuất bản.")
        elif payload.expire_at and not payload.publish_at and payload.expire_at <= now:
            raise BadRequestException(message="Thời điểm hết hạn hiển thị (expire_at) phải ở trong tương lai.")

        # 5. Tự động tính số từ & thời gian đọc
        word_count = 0
        reading_time = 0
        if ref_trans and ref_trans.content:
            text_content = re.sub(r'<[^>]+>', ' ', ref_trans.content)
            words = text_content.split()
            word_count = len(words)
            reading_time = max(1, math.ceil(word_count / 200))

        # 6. Khởi tạo đối tượng Article
        published_at = None
        if payload.status == ArticleStatus.PUBLISHED:
            published_at = payload.publish_at or now

        article = Article(
            category_id=category_id,
            department_id=payload.department_id,
            program_id=payload.program_id,
            article_type=payload.article_type,
            author_id=current_user.id,
            thumbnail_object_key=payload.thumbnail_object_key,
            cover_object_key=payload.cover_object_key,
            status=payload.status,
            is_pinned=payload.is_pinned,
            is_draft=payload.is_draft,
            word_count=word_count,
            reading_time=reading_time,
            publish_at=payload.publish_at or (published_at if payload.status == ArticleStatus.PUBLISHED else None),
            published_at=published_at,
            expire_at=payload.expire_at,
        )



        # Gán tags và tăng usage_count
        if tags_list:
            article.tags = tags_list
            for t in tags_list:
                t.usage_count += 1
                db.add(t)

        db.add(article)
        await db.flush()  # Để lấy ID bài viết

        # 7. Ghi translations
        from app.modules.language.models import Language
        from app.modules.article.models import ArticleTranslation
        for lang_code, trans_item in payload.translations.items():
            if trans_item is None:
                continue
            lang_query = select(Language.id).where(Language.code == lang_code)
            lang_res = await db.execute(lang_query)
            lang_id = lang_res.scalar()
            if not lang_id:
                continue
                
            trans_slug = trans_item.slug.strip() if trans_item.slug else slugify(trans_item.title)
            trans_slug = await self._resolve_unique_slug(db, trans_slug, lang_id)
            
            translation = ArticleTranslation(
                article_id=article.id,
                language_id=lang_id,
                title=trans_item.title,
                slug=trans_slug,
                excerpt=trans_item.excerpt,
                content=trans_item.content,
                seo_title=trans_item.seo_title,
                seo_description=trans_item.seo_description,
                canonical_url=trans_item.canonical_url,
                robots=trans_item.robots,
                og_title=trans_item.og_title,
                og_description=trans_item.og_description,
                og_image=trans_item.og_image
            )
            db.add(translation)
            
        await db.flush()

        # 8. Ghi nhận Audit Log
        from app.modules.audit.service import log_action
        log_title = "Chưa dịch"
        vi_trans = payload.translations.get("vi")
        ref_trans = vi_trans or (list(payload.translations.values())[0] if payload.translations else None)
        if ref_trans:
            log_title = ref_trans.title
        await log_action(
            db,
            current_user,
            "ARTICLE_CREATED",
            "article",
            article.id,
            {"title": log_title, "status": article.status.value}
        )
        
        await db.commit()
        db.expire(article, ["translations", "category", "tags"])

        # Load lại đầy đủ quan hệ để trả về đúng DTO
        from app.modules.category.models import CategoryTranslation
        from app.modules.tag.models import TagTranslation
        stmt = (
            select(Article)
            .where(Article.id == article.id)
            .options(
                joinedload(Article.category).options(
                    selectinload(Category.translations).selectinload(CategoryTranslation.language)
                ),
                joinedload(Article.author).joinedload(User.avatar),
                joinedload(Article.author).load_only(User.id, User.username, User.full_name, User.avatar_url),
                selectinload(Article.tags).options(
                    selectinload(Tag.translations).selectinload(TagTranslation.language)
                ),
                selectinload(Article.translations).selectinload(ArticleTranslation.language)
            )
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def check_slug_availability(
        self,
        db: AsyncSession,
        slug: str
    ) -> SlugCheckResponse:
        """
        Kiểm tra xem một slug đã tồn tại hay chưa, và gợi ý slug mới nếu trùng.
        """
        cleaned_slug = slugify(slug.strip()) if slug.strip() else "bai-viet"
        
        # Kiểm tra sự tồn tại trong DB (trên các bài viết chưa bị xóa)
        from app.modules.article.models import ArticleTranslation
        stmt = (
            select(ArticleTranslation.id)
            .join(Article, Article.id == ArticleTranslation.article_id)
            .where(
                ArticleTranslation.slug == cleaned_slug,
                Article.deleted_at == None
            )
        )
        res = await db.execute(stmt)
        exists = res.scalars().first() is not None
        
        if not exists:
            return SlugCheckResponse(available=True, suggested_slug=cleaned_slug)
            
        # Nếu đã tồn tại, chạy vòng lặp tìm hậu tố số
        suggested_slug = cleaned_slug
        counter = 1
        while True:
            suggested_slug = f"{cleaned_slug}-{counter}"
            dup_stmt = (
                select(ArticleTranslation.id)
                .join(Article, Article.id == ArticleTranslation.article_id)
                .where(
                    ArticleTranslation.slug == suggested_slug,
                    Article.deleted_at == None
                )
            )
            dup_res = await db.execute(dup_stmt)
            if not dup_res.scalars().first():
                break
            counter += 1
            
        return SlugCheckResponse(available=False, suggested_slug=suggested_slug)

    async def list_my_drafts(
        self,
        db: AsyncSession,
        *,
        current_user: Any,
        page: int = 1,
        page_size: int = 10
    ) -> tuple[list[Article], int]:
        """
        Lấy danh sách các bài viết nháp (DRAFT) của chính tác giả đang đăng nhập.
        """
        from app.modules.category.models import CategoryTranslation
        from app.modules.tag.models import TagTranslation
        
        offset = (page - 1) * page_size
        
        # Query items
        stmt = (
            select(Article)
            .where(
                Article.author_id == current_user.id,
                Article.is_draft == True,
                Article.deleted_at == None
            )
            .options(
                joinedload(Article.category).options(
                    selectinload(Category.translations).selectinload(CategoryTranslation.language)
                ),
                joinedload(Article.author).joinedload(User.avatar),
                joinedload(Article.author).load_only(User.id, User.username, User.full_name, User.avatar_url),
                selectinload(Article.tags).options(
                    selectinload(Tag.translations).selectinload(TagTranslation.language)
                ),
                selectinload(Article.translations).selectinload(ArticleTranslation.language)
            )
            .order_by(Article.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await db.execute(stmt)
        items = list(result.scalars().all())

        # Query total count
        count_stmt = select(func.count(Article.id)).where(
            Article.author_id == current_user.id,
            Article.is_draft == True,
            Article.deleted_at == None
        )
        count_res = await db.execute(count_stmt)
        total = count_res.scalar() or 0

        return items, total

    async def count_my_drafts(
        self,
        db: AsyncSession,
        *,
        current_user: Any
    ) -> int:
        """
        Đếm tổng số bài viết nháp (DRAFT) của chính tác giả đang đăng nhập.
        """
        stmt = select(func.count(Article.id)).where(
            Article.author_id == current_user.id,
            Article.is_draft == True,
            Article.deleted_at == None
        )
        res = await db.execute(stmt)
        return res.scalar() or 0

    async def get_article_detail(
        self,
        db: AsyncSession,
        *,
        article_id: uuid.UUID,
        current_user: Any,
        lang: str = "vi"
    ) -> Article:
        """
        Lấy thông tin chi tiết đầy đủ của một bài viết (áp dụng bảo mật nháp).
        """
        from app.modules.article.models import ArticleTranslation
        from app.modules.category.models import CategoryTranslation
        from app.modules.tag.models import TagTranslation

        stmt = (
            select(Article)
            .where(Article.id == article_id, Article.deleted_at == None)
            .options(
                joinedload(Article.category).options(
                    selectinload(Category.translations).selectinload(CategoryTranslation.language)
                ),
                joinedload(Article.author).joinedload(User.avatar),
                joinedload(Article.author).load_only(User.id, User.username, User.full_name, User.avatar_url),
                selectinload(Article.tags).options(
                    selectinload(Tag.translations).selectinload(TagTranslation.language)
                ),
                selectinload(Article.translations).selectinload(ArticleTranslation.language)
            )
        )
        result = await db.execute(stmt)
        article = result.scalars().first()

        if not article:
            raise NotFoundException(message="Không tìm thấy bài viết hoặc bài viết đã bị xóa.")

        # Phân quyền bản nháp (DRAFT): chỉ tác giả của bản nháp mới được quyền đọc
        if article.is_draft and article.author_id != current_user.id:
            raise ForbiddenException(message="Quyền truy cập bị từ chối. Bạn không được quyền xem bản nháp của tác giả khác.")

        # Apply translation phẳng
        self._apply_translation(article, lang=lang)
        if article.category:
            from app.modules.category.service import category_service
            category_service._apply_translation(article.category, lang=lang)
        for tag in article.tags:
            from app.modules.tag.service import tag_service
            tag_service._apply_translation(tag, lang=lang)

        return article

    async def update_article(
        self,
        db: AsyncSession,
        *,
        article_id: uuid.UUID,
        payload: ArticleUpdateRequest,
        current_user: Any,
    ) -> Article:
        """
        Cập nhật toàn bộ bài viết (bao gồm cả trạng thái nháp, danh mục, tags, và các bản dịch).
        """
        # 1. Tìm bài viết kèm theo tags, category, author, translations
        from app.modules.article.models import ArticleTranslation
        from app.modules.category.models import CategoryTranslation
        from app.modules.tag.models import TagTranslation
        
        stmt = (
            select(Article)
            .where(Article.id == article_id, Article.deleted_at == None)
            .options(
                joinedload(Article.category).options(
                    selectinload(Category.translations).selectinload(CategoryTranslation.language)
                ),
                joinedload(Article.author).joinedload(User.avatar),
                joinedload(Article.author).load_only(User.id, User.username, User.full_name, User.avatar_url),
                selectinload(Article.tags).options(
                    selectinload(Tag.translations).selectinload(TagTranslation.language)
                ),
                selectinload(Article.translations).selectinload(ArticleTranslation.language)
            )
        )
        result = await db.execute(stmt)
        article = result.scalars().first()

        if not article:
            raise NotFoundException(message="Không tìm thấy bài viết hoặc bài viết đã bị xóa.")

        # 2. Phân quyền chỉnh sửa (Edit Security)
        if article.author_id != current_user.id:
            raise ForbiddenException(message="Bạn không có quyền chỉnh sửa bài viết của tác giả khác.")

        # Tự động trích xuất category_id từ object category nếu category_id là None
        category_id = payload.category_id
        if category_id is None and payload.category and isinstance(payload.category, dict):
            try:
                category_id = uuid.UUID(str(payload.category.get("id")))
            except (ValueError, TypeError):
                pass

        # Tự động trích xuất tag_ids từ list tags nếu tag_ids là None
        tag_ids = payload.tag_ids
        if tag_ids is None and payload.tags and isinstance(payload.tags, list):
            tag_ids = []
            for t in payload.tags:
                if isinstance(t, dict) and t.get("id"):
                    try:
                        tag_ids.append(uuid.UUID(str(t.get("id"))))
                    except (ValueError, TypeError):
                        pass

        # 3. Kiểm tra Category & Content nếu bài viết được xuất bản/lên lịch (không phải nháp)
        target_is_draft = payload.is_draft if payload.is_draft is not None else article.is_draft
        target_status = payload.status if payload.status is not None else article.status
        target_category_id = category_id if category_id is not None else article.category_id

        # Tìm bản dịch tiếng Việt để validate content
        vi_trans_item = None
        if payload.translations:
            vi_trans_item = payload.translations.get("vi")
        if not vi_trans_item:
            # Fallback tìm bản dịch vi đã lưu trước đó
            for t in article.translations:
                if t.language and t.language.code == "vi":
                    vi_trans_item = t
                    break

        if not target_is_draft:
            if not target_category_id:
                raise BadRequestException(message="Danh mục là bắt buộc khi xuất bản hoặc lên lịch bài viết.")
            if not vi_trans_item or not vi_trans_item.content or not vi_trans_item.content.strip():
                raise BadRequestException(message="Nội dung bài viết không được để trống khi xuất bản hoặc lên lịch.")

        if category_id is not None:
            if category_id:
                cat_stmt = select(Category).where(Category.id == category_id, Category.deleted_at == None)
                cat_res = await db.execute(cat_stmt)
                category = cat_res.scalars().first()
                if not category:
                    raise BadRequestException(message="Danh mục không tồn tại hoặc đã bị xóa.")
                article.category_id = category_id
            else:
                article.category_id = None

        # 4. Kiểm tra Validation cho tags nếu có truyền
        tags_list = []
        if tag_ids is not None:
            if tag_ids:
                tags_stmt = select(Tag).where(Tag.id.in_(tag_ids), Tag.deleted_at == None)
                tags_res = await db.execute(tags_stmt)
                tags_list = list(tags_res.scalars().all())
                if len(tags_list) != len(tag_ids):
                    raise BadRequestException(message="Một hoặc nhiều thẻ tag không tồn tại hoặc đã bị xóa.")
            else:
                tags_list = []

        # 5. Kiểm tra thời gian lên lịch SCHEDULED
        now = datetime.now(timezone.utc)
        if target_status == ArticleStatus.SCHEDULED and not target_is_draft:
            target_publish_at = payload.publish_at if payload.publish_at is not None else article.publish_at
            if not target_publish_at:
                raise BadRequestException(message="Yêu cầu truyền thời gian xuất bản (publish_at) khi lên lịch.")
            if target_publish_at <= now:
                raise BadRequestException(message="Thời gian lên lịch xuất bản (publish_at) phải ở trong tương lai.")

        # 6. Cập nhật các trường phi ngôn ngữ
        if payload.status is not None:
            article.status = payload.status
        if payload.is_draft is not None:
            article.is_draft = payload.is_draft
        if payload.is_pinned is not None:
            article.is_pinned = payload.is_pinned
        if payload.thumbnail_object_key is not None:
            article.thumbnail_object_key = payload.thumbnail_object_key
        if payload.cover_object_key is not None:
            article.cover_object_key = payload.cover_object_key
        if "department_id" in payload.model_fields_set:
            article.department_id = payload.department_id
        if "program_id" in payload.model_fields_set:
            article.program_id = payload.program_id
        if payload.article_type is not None:
            article.article_type = payload.article_type
        
        # publish_at & published_at
        published_at = article.published_at
        if not article.published_at and target_status == ArticleStatus.PUBLISHED and not target_is_draft:
            published_at = now
        article.published_at = published_at
        
        if payload.publish_at is not None:
            article.publish_at = payload.publish_at
        elif target_status == ArticleStatus.PUBLISHED:
            article.publish_at = published_at
            
        if payload.expire_at is not None:
            article.expire_at = payload.expire_at
        article.last_edited_at = now

        # 7. Cập nhật các bản dịch trong ArticleTranslation
        from app.modules.language.models import Language
        if payload.translations is not None:
            for lang_code, trans_item in payload.translations.items():
                if trans_item is None:
                    continue
                lang_query = select(Language.id).where(Language.code == lang_code)
                lang_res = await db.execute(lang_query)
                lang_id = lang_res.scalar()
                if not lang_id:
                    continue

                stmt_trans = select(ArticleTranslation).where(
                    ArticleTranslation.article_id == article_id,
                    ArticleTranslation.language_id == lang_id
                )
                trans_res = await db.execute(stmt_trans)
                translation = trans_res.scalar_one_or_none()

                trans_slug = trans_item.slug.strip() if trans_item.slug else slugify(trans_item.title)
                trans_slug = await self._resolve_unique_slug(db, trans_slug, lang_id, exclude_article_id=article_id)

                if translation:
                    translation.title = trans_item.title
                    translation.slug = trans_slug
                    translation.excerpt = trans_item.excerpt
                    translation.content = trans_item.content
                    translation.seo_title = trans_item.seo_title
                    translation.seo_description = trans_item.seo_description
                    translation.canonical_url = trans_item.canonical_url
                    translation.robots = trans_item.robots
                    translation.og_title = trans_item.og_title
                    translation.og_description = trans_item.og_description
                    translation.og_image = trans_item.og_image
                else:
                    translation = ArticleTranslation(
                        article_id=article_id,
                        language_id=lang_id,
                        title=trans_item.title,
                        slug=trans_slug,
                        excerpt=trans_item.excerpt,
                        content=trans_item.content,
                        seo_title=trans_item.seo_title,
                        seo_description=trans_item.seo_description,
                        canonical_url=trans_item.canonical_url,
                        robots=trans_item.robots,
                        og_title=trans_item.og_title,
                        og_description=trans_item.og_description,
                        og_image=trans_item.og_image
                    )
                db.add(translation)

                # Tính toán lại word_count & reading_time nếu là vi
                if lang_code == "vi" and trans_item.content:
                    text_content = re.sub(r'<[^>]+>', ' ', trans_item.content)
                    words = text_content.split()
                    article.word_count = len(words)
                    article.reading_time = max(1, math.ceil(article.word_count / 200))

        # 8. Cập nhật Tags và usage_count (chỉ thực hiện nếu tag_ids được truyền lên)
        if tag_ids is not None:
            # Lấy danh sách tags cũ
            old_tags = list(article.tags)
            old_tag_ids = {t.id for t in old_tags}
            new_tag_ids = {t.id for t in tags_list}

            # Gỡ các tag không còn dùng nữa
            tags_to_remove = [t for t in old_tags if t.id not in new_tag_ids]
            for t in tags_to_remove:
                article.tags.remove(t)
                # Giảm usage_count
                t.usage_count = max(0, t.usage_count - 1)
                db.add(t)

            # Thêm các tag mới vào
            tags_to_add = [t for t in tags_list if t.id not in old_tag_ids]
            for t in tags_to_add:
                article.tags.append(t)
                # Tăng usage_count
                t.usage_count += 1
                db.add(t)

        db.add(article)
        await db.commit()
        db.expire(article, ["translations", "category", "tags"])

        # Load lại đầy đủ quan hệ để trả về đúng DTO
        stmt_reload = (
            select(Article)
            .where(Article.id == article.id)
            .options(
                joinedload(Article.category).options(
                    selectinload(Category.translations).selectinload(CategoryTranslation.language)
                ),
                joinedload(Article.author).joinedload(User.avatar),
                joinedload(Article.author).load_only(User.id, User.username, User.full_name, User.avatar_url),
                selectinload(Article.tags).options(
                    selectinload(Tag.translations).selectinload(TagTranslation.language)
                ),
                selectinload(Article.translations).selectinload(ArticleTranslation.language)
            )
        )
        result_reload = await db.execute(stmt_reload)
        article_reloaded = result_reload.scalars().first()

        # 9. Ghi nhận audit log
        from app.modules.audit.service import log_action
        log_title = "Chưa dịch"
        for t in getattr(article_reloaded, "translations", []):
            if t.language and t.language.code == "vi":
                log_title = t.title
                break
        await log_action(
            db,
            current_user,
            "ARTICLE_UPDATED",
            "article",
            article_reloaded.id,
            {"title": log_title, "status": article_reloaded.status.value, "is_draft": article_reloaded.is_draft}
        )

        return article_reloaded

    async def list_articles_portal(
        self,
        db: AsyncSession,
        *,
        category_slug: str,
        page: int = 1,
        page_size: int = 10,
        lang: str = "vi",
    ) -> Tuple[list[Article], int]:
        """
        Query danh sách bài viết công khai thuộc một danh mục cụ thể cho Portal FE Client.
        Truy vấn tối ưu hóa, hỗ trợ phân trang và nạp sẵn (avoid N+1) đầy đủ SEO metadata.
        """
        # 1. Tìm Category theo slug (hỗ trợ slug gốc hoặc slug bản dịch)
        from app.modules.category.models import CategoryTranslation
        cat_stmt = (
            select(Category)
            .outerjoin(CategoryTranslation)
            .where(
                CategoryTranslation.slug == category_slug,
                Category.deleted_at.is_(None)
            )
            .limit(1)
        )
        cat_res = await db.execute(cat_stmt)
        category = cat_res.scalars().first()
        if not category:
            raise NotFoundException(message=f"Không tìm thấy danh mục '{category_slug}'.")

        # 2. Xây dựng Query lấy danh sách bài viết
        # Điều kiện: thuộc category, đã PUBLISHED, không bị xóa mềm, và publish_at <= hiện tại
        now = datetime.now(timezone.utc)
        
        stmt = (
            select(Article)
            .where(
                Article.category_id == category.id,
                Article.status == ArticleStatus.PUBLISHED,
                Article.deleted_at == None,
                Article.publish_at <= now
            )
        )
        
        # Query count
        count_stmt = (
            select(func.count(Article.id))
            .where(
                Article.category_id == category.id,
                Article.status == ArticleStatus.PUBLISHED,
                Article.deleted_at == None,
                Article.publish_at <= now
            )
        )
        count_res = await db.execute(count_stmt)
        total = count_res.scalar() or 0

        # 3. Nạp trước các quan hệ (Eager Loading)
        stmt = stmt.options(
            joinedload(Article.category).load_only(Category.id),
            joinedload(Article.author).joinedload(User.avatar),
            joinedload(Article.author).load_only(User.id, User.username, User.full_name, User.avatar_url),
            selectinload(Article.tags).load_only(Tag.id, Tag.color)
        )

        # 4. Sắp xếp: Ghim lên đầu (is_pinned DESC), sau đó đến ngày công bố mới nhất (publish_at DESC)
        stmt = stmt.order_by(Article.is_pinned.desc(), Article.publish_at.desc())

        # 5. Phân trang
        skip = (page - 1) * page_size
        stmt = stmt.offset(skip).limit(page_size)

        # 6. Thực thi
        result = await db.execute(stmt)
        items = list(result.scalars().all())

        # Apply translations phẳng cho kết quả đầu ra
        for item in items:
            self._apply_translation(item, lang=lang)
            if item.category:
                from app.modules.category.service import category_service
                category_service._apply_translation(item.category, lang=lang)
            for tag in item.tags:
                from app.modules.tag.service import tag_service
                tag_service._apply_translation(tag, lang=lang)

        return items, total

    async def get_article_by_slug_portal(
        self,
        db: AsyncSession,
        slug: str,
        lang: str = "vi",
        guest_uuid: Optional[str] = None,
        client_ip: Optional[str] = None,
        redis_client: Optional[Any] = None,
    ) -> Article:
        """
        Lấy chi tiết một bài viết công khai theo slug cho Portal FE Client.
        Tự động tăng view_count của bài viết lên 1 nếu là lượt xem mới (kiểm tra qua Redis).
        """
        now = datetime.now(timezone.utc)
        from app.modules.language.models import Language
        from app.modules.article.models import ArticleTranslation
        from app.modules.category.models import CategoryTranslation
        from app.modules.tag.models import TagTranslation
        
        lang_res = await db.execute(select(Language.id).where(Language.code == lang))
        lang_id = lang_res.scalar()
        if not lang_id:
            lang_res = await db.execute(select(Language.id).where(Language.code == "vi"))
            lang_id = lang_res.scalar()

        # Câu query lấy chi tiết bài viết (Eager loading tối ưu)
        stmt = (
            select(Article)
            .join(ArticleTranslation, (ArticleTranslation.article_id == Article.id) & (ArticleTranslation.language_id == lang_id), isouter=True)
            .where(
                ArticleTranslation.slug == slug,
                Article.status == ArticleStatus.PUBLISHED,
                Article.deleted_at == None,
                Article.publish_at <= now
            )
            .options(
                joinedload(Article.category).options(
                    selectinload(Category.translations).selectinload(CategoryTranslation.language)
                ),
                joinedload(Article.author).joinedload(User.avatar),
                joinedload(Article.author).load_only(User.id, User.username, User.full_name, User.avatar_url),
                selectinload(Article.tags).options(
                    selectinload(Tag.translations).selectinload(TagTranslation.language)
                ),
                selectinload(Article.translations).selectinload(ArticleTranslation.language)
            )
        )
        
        result = await db.execute(stmt)
        article = result.scalars().first()
        if not article:
            raise NotFoundException(message=f"Không tìm thấy bài viết hoặc bài viết chưa được công bố.")

        # 2. Tăng view_count tự động nếu là lượt xem mới
        if redis_client:
            guest_key = f"view_limit:article:{article.id}:guest:{guest_uuid}" if guest_uuid else None
            ip_key = f"view_limit:article:{article.id}:ip:{client_ip}" if client_ip else None
            
            # Kiểm tra xem guest_uuid hoặc IP đã xem bài viết này chưa
            has_viewed = False
            if guest_key and await redis_client.exists(guest_key):
                has_viewed = True
            if not has_viewed and ip_key and await redis_client.exists(ip_key):
                has_viewed = True

            if not has_viewed:
                # Tăng view trong DB thực tế
                article.view_count += 1
                db.add(article)
                await db.commit()
                
                # Lưu trạng thái xem vào Redis để chống spam
                if guest_key:
                    await redis_client.set(guest_key, "1", ex=86400) # 24 giờ cho Guest
                if ip_key:
                    await redis_client.set(ip_key, "1", ex=180)     # 3 phút cho IP
        else:
            article.view_count += 1
            db.add(article)
            await db.commit()

        # Apply translation phẳng
        self._apply_translation(article, lang=lang)
        if article.category:
            from app.modules.category.service import category_service
            category_service._apply_translation(article.category, lang=lang)
        for tag in article.tags:
            from app.modules.tag.service import tag_service
            tag_service._apply_translation(tag, lang=lang)

        return article

    async def list_all_articles_portal(
        self,
        db: AsyncSession,
        *,
        page: int = 1,
        page_size: int = 10,
        search: Optional[str] = None,
        category_slug: Optional[str] = None,
        department_id: Optional[uuid.UUID] = None,
        program_id: Optional[uuid.UUID] = None,
        article_type: Optional[str] = None,
        category_slugs: Optional[list[str]] = None,
        exclude_category_slugs: Optional[list[str]] = None,
        tag_slug: Optional[str] = None,
        author_username: Optional[str] = None,
        is_pinned: Optional[bool] = None,
        has_thumbnail: Optional[bool] = None,
        published_from: Optional[datetime] = None,
        published_to: Optional[datetime] = None,
        sort_by: str = "publish_at",
        sort_dir: str = "desc",
        lang: str = "vi",
    ) -> Tuple[list[Article], int]:
        """
        Query danh sách tất cả các bài viết công khai cho Portal FE Client.
        Hỗ trợ tìm kiếm, lọc theo slugs/flags, phân trang số và sắp xếp động tối ưu.
        """
        builder = ArticleQueryBuilder(db)
        
        # Lấy language_id cho resolved_translation
        from app.modules.language.models import Language
        lang_res = await db.execute(select(Language.id).where(Language.code == lang))
        lang_id = lang_res.scalar()
        if not lang_id:
            lang_res = await db.execute(select(Language.id).where(Language.code == "vi"))
            lang_id = lang_res.scalar()

        if lang_id:
            builder.resolve_translation(lang_id)

        # Áp dụng Portal scope và eager load quan hệ
        builder.public_scope()
        builder.with_portal_relations()
        
        # Đóng gói filter params
        filter_params = ArticleFilterParams(
            category_slug=category_slug,
            category_slugs=category_slugs,
            exclude_category_slugs=exclude_category_slugs,
            tag_slug=tag_slug,
            author_username=author_username,
            is_pinned=is_pinned,
            has_thumbnail=has_thumbnail,
            published_from=published_from,
            published_to=published_to
        )
        builder.filter(filter_params)
        if department_id:
            builder.query = builder.query.where(Article.department_id == department_id)
        if program_id:
            builder.query = builder.query.where(Article.program_id == program_id)
        if article_type:
            builder.query = builder.query.where(Article.article_type == article_type)
        
        # Tìm kiếm Generic
        if search:
            builder.search(
                fields=[ArticleTranslation.title, ArticleTranslation.excerpt, ArticleTranslation.content],
                keyword=search
            )
            
        # Đếm tổng
        total = await builder.get_total_count()
        
        # Định đoạt Sort Strategy
        if sort_by != "publish_at":
            strategy = SortStrategy.CUSTOM
        elif search:
            strategy = SortStrategy.SEARCH
        elif category_slug:
            strategy = SortStrategy.CATEGORY
        else:
            strategy = SortStrategy.HOME
            
        builder.sort(
            strategy=strategy,
            sort_by=sort_by,
            sort_dir=sort_dir
        )
        builder.paginate(page=page, page_size=page_size)
        
        # Thực thi
        items = await builder.execute()

        # Apply translations phẳng cho kết quả đầu ra
        for item in items:
            self._apply_translation(item, lang=lang)
            if item.category:
                from app.modules.category.service import category_service
                category_service._apply_translation(item.category, lang=lang)
            for tag in item.tags:
                from app.modules.tag.service import tag_service
                tag_service._apply_translation(tag, lang=lang)

        return items, total
    async def delete_article(
        self,
        db: AsyncSession,
        *,
        article_id: uuid.UUID,
        current_user: Any
    ) -> None:
        """
        Xóa mềm bài viết bằng cách gán deleted_at.
        """
        article = await self.get_article_detail(db, article_id=article_id, current_user=current_user)
        
        article.deleted_at = datetime.now(timezone.utc)
        db.add(article)
        await db.flush()

        # Ghi nhận audit log
        from app.modules.audit.service import log_action
        log_title = "Chưa dịch"
        for t in getattr(article, "translations", []):
            if t.language and t.language.code == "vi":
                log_title = t.title
                break
        await log_action(
            db,
            current_user,
            "ARTICLE_DELETED",
            "article",
            article.id,
            {"title": log_title}
        )
        await db.commit()
        logger.info(f"Soft deleted Article: id={article_id} by user {current_user.id}")
    async def restore_article(
        self,
        db: AsyncSession,
        *,
        article_id: uuid.UUID,
        current_user: Any
    ) -> Article:
        """
        Khôi phục bài viết đã bị xóa mềm (deleted_at != None).
        """
        from app.modules.category.models import CategoryTranslation
        from app.modules.tag.models import TagTranslation
        from app.modules.article.models import ArticleTranslation

        # Query cả bài viết đã xóa (không lọc deleted_at == None)
        stmt = (
            select(Article)
            .where(Article.id == article_id)
            .options(
                joinedload(Article.category).options(
                    selectinload(Category.translations).selectinload(CategoryTranslation.language)
                ),
                joinedload(Article.author).joinedload(User.avatar),
                joinedload(Article.author).load_only(User.id, User.username, User.full_name, User.avatar_url),
                selectinload(Article.tags).options(
                    selectinload(Tag.translations).selectinload(TagTranslation.language)
                ),
                selectinload(Article.translations).selectinload(ArticleTranslation.language)
            )
        )
        result = await db.execute(stmt)
        article = result.scalars().first()
        
        if not article:
            raise NotFoundException(message="Không tìm thấy bài viết.")

        if article.deleted_at is not None:
            article.deleted_at = None
            article.last_edited_at = datetime.now(timezone.utc)
            db.add(article)
            await db.flush()

            # Ghi nhận audit log
            from app.modules.audit.service import log_action
            log_title = "Chưa dịch"
            for t in getattr(article, "translations", []):
                if t.language and t.language.code == "vi":
                    log_title = t.title
                    break
            await log_action(
                db,
                current_user,
                "ARTICLE_RESTORED",
                "article",
                article.id,
                {"title": log_title}
            )
            await db.commit()
            logger.info(f"Restored Article: id={article_id} by user {current_user.id}")

        return article


article_service = ArticleService()


