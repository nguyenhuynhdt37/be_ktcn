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

from sqlalchemy import select, func, desc, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload, load_only

from app.core.exceptions import BadRequestException, NotFoundException, ForbiddenException
from app.modules.article.models import Article, ArticleStatus
from app.modules.article.schemas import BulkActionEnum, BulkActionResponse, ArticleStatsResponse, ArticleAttributesUpdateRequest, ArticleCreateRequest, SlugCheckResponse, ArticleDetailResponse, ArticleDraftsCountResponse, ArticleUpdateRequest
from app.modules.auth.models import User
from app.modules.category.models import Category
from app.modules.tag.models import Tag


class ArticleService:
    """
    Business logic phục vụ cho module Articles.
    """

    async def list_articles(
        self,
        db: AsyncSession,
        *,
        page: int = 1,
        page_size: int = 10,
        search: Optional[str] = None,
        category_id: Optional[uuid.UUID] = None,
        author_id: Optional[uuid.UUID] = None,
        tag_ids: Optional[list[uuid.UUID]] = None,
        status: Optional[ArticleStatus] = None,
        is_featured: Optional[bool] = None,
        is_pinned: Optional[bool] = None,
        is_draft: Optional[bool] = False,
        created_from: Optional[datetime] = None,
        created_to: Optional[datetime] = None,
        published_from: Optional[datetime] = None,
        published_to: Optional[datetime] = None,
        deleted: bool = False,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
    ) -> Tuple[list[Article], int]:
        """
        Query danh sách bài viết từ database với phân trang, lọc và sắp xếp động tối ưu.
        """
        skip = (page - 1) * page_size

        # 1. Khởi tạo Query Builder
        query = select(Article)
        count_query = select(func.count(Article.id))

        # 2. Xử lý bộ lọc Soft Delete (deleted parameter)
        if deleted:
            query = query.where(Article.deleted_at != None)
            count_query = count_query.where(Article.deleted_at != None)
        else:
            query = query.where(Article.deleted_at == None)
            count_query = count_query.where(Article.deleted_at == None)

        # 3. Xử lý bộ lọc Trạng thái (status)
        # Chỉ hiển thị bài viết khác DRAFT. Không cho phép query DRAFT qua API này.
        if status:
            if status == ArticleStatus.DRAFT:
                # Trả về rỗng nếu cố tình query DRAFT
                query = query.where(Article.status == None)
                count_query = count_query.where(Article.status == None)
            else:
                query = query.where(Article.status == status)
                count_query = count_query.where(Article.status == status)
        else:
            query = query.where(Article.status != ArticleStatus.DRAFT)
            count_query = count_query.where(Article.status != ArticleStatus.DRAFT)

        # 4. Xử lý lọc theo Danh mục (category_id)
        if category_id:
            query = query.where(Article.category_id == category_id)
            count_query = count_query.where(Article.category_id == category_id)

        # 5. Xử lý lọc theo Tác giả (author_id)
        if author_id:
            query = query.where(Article.author_id == author_id)
            count_query = count_query.where(Article.author_id == author_id)

        # 6. Xử lý lọc theo Tags (tag_ids - hỗ trợ nhiều tag theo logic AND)
        if tag_ids:
            for t_id in tag_ids:
                query = query.where(Article.tags.any(Tag.id == t_id))
                count_query = count_query.where(Article.tags.any(Tag.id == t_id))

        # 7. Xử lý tìm kiếm (search - title hoặc slug, không phân biệt hoa thường)
        if search:
            search_filter = Article.title.ilike(f"%{search}%") | Article.slug.ilike(f"%{search}%")
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        # 8. Xử lý lọc các thuộc tính đặc biệt (is_featured, is_pinned)
        if is_featured is not None:
            query = query.where(Article.is_featured == is_featured)
            count_query = count_query.where(Article.is_featured == is_featured)
        if is_pinned is not None:
            query = query.where(Article.is_pinned == is_pinned)
            count_query = count_query.where(Article.is_pinned == is_pinned)
        if is_draft is not None:
            query = query.where(Article.is_draft == is_draft)
            count_query = count_query.where(Article.is_draft == is_draft)

        # 9. Xử lý lọc theo Khoảng thời gian tạo (created_from/created_to)
        if created_from:
            query = query.where(Article.created_at >= created_from)
            count_query = count_query.where(Article.created_at >= created_from)
        if created_to:
            query = query.where(Article.created_at <= created_to)
            count_query = count_query.where(Article.created_at <= created_to)

        # 10. Xử lý lọc theo Khoảng thời gian xuất bản (published_from/published_to)
        if published_from:
            query = query.where(Article.published_at >= published_from)
            count_query = count_query.where(Article.published_at >= published_from)
        if published_to:
            query = query.where(Article.published_at <= published_to)
            count_query = count_query.where(Article.published_at <= published_to)

        # 11. Đếm tổng số bản ghi thỏa mãn điều kiện
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # 12. Tối ưu hóa truy vấn nạp dữ liệu liên quan (Avoid N+1 & SELECT * )
        query = query.options(
            joinedload(Article.category).load_only(Category.id, Category.name, Category.slug),
            joinedload(Article.author).joinedload(User.avatar),
            joinedload(Article.author).load_only(User.id, User.username, User.full_name, User.avatar_url),
            selectinload(Article.tags).load_only(Tag.id, Tag.name, Tag.slug, Tag.color),
            load_only(
                Article.id,
                Article.title,
                Article.slug,
                Article.excerpt,
                Article.thumbnail_object_key,
                Article.status,
                Article.is_featured,
                Article.is_pinned,
                Article.is_draft,
                Article.view_count,
                Article.created_at,
                Article.publish_at,
                Article.published_at,
            )
        )

        # 13. Sắp xếp động (Sorting)
        sort_columns = {
            "title": Article.title,
            "created_at": Article.created_at,
            "updated_at": Article.updated_at,
            "published_at": Article.published_at,
            "view_count": Article.view_count,
            "sort_order": Article.sort_order,
        }
        col = sort_columns.get(sort_by, Article.created_at)
        
        # Nếu sort_by được gán là is_pinned hoặc is_featured, ta luôn ưu tiên sort_order/created_at phụ trợ.
        # Ở đây chỉ áp dụng cột chỉ định từ user
        if sort_dir.lower() == "asc":
            query = query.order_by(col.asc())
        else:
            query = query.order_by(col.desc())

        # 14. Phân trang (Pagination)
        query = query.offset(skip).limit(page_size)

        # 15. Thực thi câu lệnh SQL lấy kết quả
        result = await db.execute(query)
        items = list(result.scalars().all())

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
        stmt = (
            select(Article)
            .where(Article.id == article_id, Article.deleted_at == None)
            .options(
                joinedload(Article.category).load_only(Category.id, Category.name, Category.slug),
                joinedload(Article.author).joinedload(User.avatar),
                joinedload(Article.author).load_only(User.id, User.username, User.full_name, User.avatar_url),
                selectinload(Article.tags).load_only(Tag.id, Tag.name, Tag.slug, Tag.color)
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
        await log_action(
            db,
            current_user,
            "ARTICLE_ARCHIVED",
            "article",
            article.id,
            {"title": article.title, "previous_status": "PUBLISHED"}
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
        stmt = (
            select(Article)
            .where(Article.id == article_id, Article.deleted_at == None)
            .options(
                joinedload(Article.category).load_only(Category.id, Category.name, Category.slug),
                joinedload(Article.author).joinedload(User.avatar),
                joinedload(Article.author).load_only(User.id, User.username, User.full_name, User.avatar_url),
                selectinload(Article.tags).load_only(Tag.id, Tag.name, Tag.slug, Tag.color)
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
        await log_action(
            db,
            current_user,
            "ARTICLE_PUBLISHED",
            "article",
            article.id,
            {"title": article.title, "previous_status": "ARCHIVED"}
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
        Cập nhật nhanh các thuộc tính đặc biệt (is_featured, is_pinned) của bài viết.
        """
        stmt = (
            select(Article)
            .where(Article.id == article_id, Article.deleted_at == None)
            .options(
                joinedload(Article.category).load_only(Category.id, Category.name, Category.slug),
                joinedload(Article.author).joinedload(User.avatar),
                joinedload(Article.author).load_only(User.id, User.username, User.full_name, User.avatar_url),
                selectinload(Article.tags).load_only(Tag.id, Tag.name, Tag.slug, Tag.color)
            )
        )
        result = await db.execute(stmt)
        article = result.scalars().first()
        
        if not article:
            raise NotFoundException(message="Không tìm thấy bài viết hoặc bài viết đã bị xóa.")

        changes = {}
        if payload.is_featured is not None:
            changes["is_featured"] = {"old": article.is_featured, "new": payload.is_featured}
            article.is_featured = payload.is_featured
        
        if payload.is_pinned is not None:
            changes["is_pinned"] = {"old": article.is_pinned, "new": payload.is_pinned}
            article.is_pinned = payload.is_pinned

        if changes:
            article.last_edited_at = datetime.now(timezone.utc)
            db.add(article)
            
            # Ghi nhận audit log
            from app.modules.audit.service import log_action
            await log_action(
                db,
                current_user,
                "ARTICLE_UPDATED",
                "article",
                article.id,
                {"title": article.title, "attribute_changes": changes}
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
        Tạo bài viết mới.
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
        if not payload.is_draft:
            if not category_id:
                raise BadRequestException(message="Danh mục là bắt buộc khi xuất bản hoặc lên lịch bài viết.")
            if not payload.content or not payload.content.strip():
                raise BadRequestException(message="Nội dung bài viết không được để trống khi xuất bản hoặc lên lịch.")

        if category_id:
            cat_stmt = select(Category).where(Category.id == category_id, Category.deleted_at == None)
            cat_res = await db.execute(cat_stmt)
            category = cat_res.scalars().first()
            if not category:
                raise BadRequestException(message="Danh mục không tồn tại hoặc đã bị xóa.")

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

        # 5. Xử lý sinh Slug & tránh trùng lặp slug
        base_slug = payload.slug.strip() if (payload.slug and payload.slug.strip()) else slugify(payload.title)
        if not base_slug:
            base_slug = "bai-viet"
            
        slug = base_slug
        counter = 1
        while True:
            dup_stmt = select(Article.id).where(Article.slug == slug, Article.deleted_at == None)
            dup_res = await db.execute(dup_stmt)
            if not dup_res.scalars().first():
                break
            slug = f"{base_slug}-{counter}"
            counter += 1

        # 6. Tự động tính số từ & thời gian đọc
        word_count = 0
        reading_time = 0
        if payload.content:
            text_content = re.sub(r'<[^>]+>', ' ', payload.content)
            words = text_content.split()
            word_count = len(words)
            reading_time = max(1, math.ceil(word_count / 200))

        # 7. Khởi tạo đối tượng Article
        published_at = None
        if payload.status == ArticleStatus.PUBLISHED:
            published_at = payload.publish_at or now

        article = Article(
            category_id=category_id,
            author_id=current_user.id,
            title=payload.title,
            slug=slug,
            excerpt=payload.excerpt,
            content=payload.content or "",
            thumbnail_object_key=payload.thumbnail_object_key,
            cover_object_key=payload.cover_object_key,
            status=payload.status,
            is_featured=payload.is_featured,
            is_pinned=payload.is_pinned,
            is_draft=payload.is_draft,
            word_count=word_count,
            reading_time=reading_time,
            publish_at=payload.publish_at or (published_at if payload.status == ArticleStatus.PUBLISHED else None),
            published_at=published_at,
            expire_at=payload.expire_at,
            
            # SEO fields
            seo_title=payload.seo_title,
            seo_description=payload.seo_description,
            canonical_url=payload.canonical_url,
            robots=payload.robots,
            og_title=payload.og_title,
            og_description=payload.og_description,
            og_image=payload.og_image
        )
        
        # Gán tags và tăng usage_count
        if tags_list:
            article.tags = tags_list
            for t in tags_list:
                t.usage_count += 1
                db.add(t)

        db.add(article)
        await db.flush()  # Để lấy ID bài viết phục vụ ghi Audit Log

        # 8. Ghi nhận Audit Log
        from app.modules.audit.service import log_action
        await log_action(
            db,
            current_user,
            "ARTICLE_CREATED",
            "article",
            article.id,
            {"title": article.title, "status": article.status.value}
        )
        
        await db.commit()

        # Load lại đầy đủ quan hệ để trả về đúng DTO
        stmt = (
            select(Article)
            .where(Article.id == article.id)
            .options(
                joinedload(Article.category).load_only(Category.id, Category.name, Category.slug),
                joinedload(Article.author).joinedload(User.avatar),
                joinedload(Article.author).load_only(User.id, User.username, User.full_name, User.avatar_url),
                selectinload(Article.tags).load_only(Tag.id, Tag.name, Tag.slug, Tag.color)
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
        
        # Kiểm tra sự tồn tại trong DB
        stmt = select(Article.id).where(Article.slug == cleaned_slug, Article.deleted_at == None)
        res = await db.execute(stmt)
        exists = res.scalars().first() is not None
        
        if not exists:
            return SlugCheckResponse(available=True, suggested_slug=cleaned_slug)
            
        # Nếu đã tồn tại, chạy vòng lặp tìm hậu tố số
        suggested_slug = cleaned_slug
        counter = 1
        while True:
            suggested_slug = f"{cleaned_slug}-{counter}"
            dup_stmt = select(Article.id).where(Article.slug == suggested_slug, Article.deleted_at == None)
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
                joinedload(Article.category).load_only(Category.id, Category.name, Category.slug),
                joinedload(Article.author).joinedload(User.avatar),
                joinedload(Article.author).load_only(User.id, User.username, User.full_name, User.avatar_url),
                selectinload(Article.tags).load_only(Tag.id, Tag.name, Tag.slug, Tag.color)
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
        current_user: Any
    ) -> Article:
        """
        Lấy thông tin chi tiết đầy đủ của một bài viết (áp dụng bảo mật nháp).
        """
        stmt = (
            select(Article)
            .where(Article.id == article_id, Article.deleted_at == None)
            .options(
                joinedload(Article.category).load_only(Category.id, Category.name, Category.slug),
                joinedload(Article.author).joinedload(User.avatar),
                joinedload(Article.author).load_only(User.id, User.username, User.full_name, User.avatar_url),
                selectinload(Article.tags).load_only(Tag.id, Tag.name, Tag.slug, Tag.color)
            )
        )
        result = await db.execute(stmt)
        article = result.scalars().first()

        if not article:
            raise NotFoundException(message="Không tìm thấy bài viết hoặc bài viết đã bị xóa.")

        # Phân quyền bản nháp (DRAFT): chỉ tác giả của bản nháp mới được quyền đọc
        if article.is_draft and article.author_id != current_user.id:
            raise ForbiddenException(message="Quyền truy cập bị từ chối. Bạn không được quyền xem bản nháp của tác giả khác.")

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
        Cập nhật toàn bộ bài viết (bao gồm cả trạng thái nháp, danh mục, tags, SEO...).
        """
        # 1. Tìm bài viết kèm theo tags, category, author
        stmt = (
            select(Article)
            .where(Article.id == article_id, Article.deleted_at == None)
            .options(
                joinedload(Article.category).load_only(Category.id, Category.name, Category.slug),
                joinedload(Article.author).joinedload(User.avatar),
                joinedload(Article.author).load_only(User.id, User.username, User.full_name, User.avatar_url),
                selectinload(Article.tags).load_only(Tag.id, Tag.name, Tag.slug, Tag.color)
            )
        )
        result = await db.execute(stmt)
        article = result.scalars().first()

        if not article:
            raise NotFoundException(message="Không tìm thấy bài viết hoặc bài viết đã bị xóa.")

        # 2. Phân quyền chỉnh sửa (Edit Security):
        # Chỉ chủ sở hữu bài viết (tác giả) mới được chỉnh sửa bài viết của mình.
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
        target_content = payload.content if payload.content is not None else article.content

        if not target_is_draft:
            if not target_category_id:
                raise BadRequestException(message="Danh mục là bắt buộc khi xuất bản hoặc lên lịch bài viết.")
            if not target_content or not target_content.strip():
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

        # 6. Xử lý logic sinh slug (nếu slug bị thay đổi so với slug cũ)
        slug = article.slug
        if payload.slug and payload.slug.strip() != article.slug:
            slug = slugify(payload.slug.strip())
            # Kiểm tra trùng lặp slug với bài viết khác
            dup_stmt = select(Article.id).where(
                Article.slug == slug, 
                Article.id != article.id, 
                Article.deleted_at == None
            )
            dup_res = await db.execute(dup_stmt)
            if dup_res.scalars().first():
                # Nếu bị trùng, tự động sinh hậu tố số
                counter = 1
                base_slug = slug
                while True:
                    slug = f"{base_slug}-{counter}"
                    dup_check = select(Article.id).where(
                        Article.slug == slug,
                        Article.id != article.id,
                        Article.deleted_at == None
                    )
                    dup_check_res = await db.execute(dup_check)
                    if not dup_check_res.scalars().first():
                        break
                    counter += 1
        elif payload.title and payload.title.strip() != article.title:
            # Nếu title đổi nhưng slug không truyền -> tự động sinh slug mới
            slug = slugify(payload.title.strip())
            dup_stmt = select(Article.id).where(
                Article.slug == slug,
                Article.id != article.id,
                Article.deleted_at == None
            )
            dup_res = await db.execute(dup_stmt)
            if dup_res.scalars().first():
                counter = 1
                base_slug = slug
                while True:
                    slug = f"{base_slug}-{counter}"
                    dup_check = select(Article.id).where(
                        Article.slug == slug,
                        Article.id != article.id,
                        Article.deleted_at == None
                    )
                    dup_check_res = await db.execute(dup_check)
                    if not dup_check_res.scalars().first():
                        break
                    counter += 1

        # 7. Tính toán số từ và thời gian đọc từ content mới
        if payload.content is not None:
            content_html = payload.content
            text_content = re.sub(r'<[^>]+>', ' ', content_html)
            words = text_content.split()
            word_count = len(words)
            reading_time = max(1, math.ceil(word_count / 200))
            article.content = content_html
            article.word_count = word_count
            article.reading_time = reading_time

        # 8. Cập nhật các trường
        if payload.title is not None:
            article.title = payload.title
        article.slug = slug
        if payload.excerpt is not None:
            article.excerpt = payload.excerpt
        if payload.status is not None:
            article.status = payload.status
        if payload.is_draft is not None:
            article.is_draft = payload.is_draft
        if payload.is_featured is not None:
            article.is_featured = payload.is_featured
        if payload.is_pinned is not None:
            article.is_pinned = payload.is_pinned
        if payload.thumbnail_object_key is not None:
            article.thumbnail_object_key = payload.thumbnail_object_key
        if payload.cover_object_key is not None:
            article.cover_object_key = payload.cover_object_key
        
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

        # SEO
        if payload.seo_title is not None:
            article.seo_title = payload.seo_title
        if payload.seo_description is not None:
            article.seo_description = payload.seo_description
        if payload.canonical_url is not None:
            article.canonical_url = payload.canonical_url
        if payload.robots is not None:
            article.robots = payload.robots
        if payload.og_title is not None:
            article.og_title = payload.og_title
        if payload.og_description is not None:
            article.og_description = payload.og_description
        if payload.og_image is not None:
            article.og_image = payload.og_image

        # 9. Cập nhật Tags và usage_count (chỉ thực hiện nếu tag_ids được truyền lên)
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
        await db.refresh(article)

        # 10. Ghi nhận audit log
        from app.modules.audit.service import log_action
        await log_action(
            db,
            current_user,
            "ARTICLE_UPDATED",
            "article",
            article.id,
            {"title": article.title, "status": article.status.value, "is_draft": article.is_draft}
        )

        return article


article_service = ArticleService()
