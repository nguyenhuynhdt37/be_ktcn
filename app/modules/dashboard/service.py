from datetime import datetime, timezone, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.modules.dashboard.schemas import (
    ArticleStats,
    ConsultationStats,
    ContentStats,
    DashboardResponse,
    LoginStats,
    RecentActivityItem,
    TopArticleItem,
    UserStats,
    VisitorStats,
)


class DashboardService:
    """Service tổng hợp dữ liệu cho Admin Dashboard."""

    async def get_dashboard(
        self, db: AsyncSession, redis_client: aioredis.Redis
    ) -> DashboardResponse:
        """Lấy toàn bộ thống kê hệ thống trong 1 lần gọi."""
        visitors = await self._get_visitor_stats(redis_client, db)
        articles = await self._get_article_stats(db)
        users = await self._get_user_stats(db)
        consultations = await self._get_consultation_stats(db)
        content = await self._get_content_stats(db)
        logins = await self._get_login_stats(db)
        top_articles = await self._get_top_articles(db)
        recent_activities = await self._get_recent_activities(db)

        return DashboardResponse(
            visitors=visitors,
            articles=articles,
            users=users,
            consultations=consultations,
            content=content,
            logins=logins,
            top_articles=top_articles,
            recent_activities=recent_activities,
        )

    async def _get_visitor_stats(
        self, redis_client: aioredis.Redis, db: AsyncSession
    ) -> VisitorStats:
        """Reuse logic từ StatisticsService."""
        from app.modules.statistics.service import statistics_service

        stats = await statistics_service.get_stats(redis_client, db)
        return VisitorStats(
            online_count=stats["online_count"],
            total_visits=stats["total_visits"],
        )

    async def _get_article_stats(self, db: AsyncSession) -> ArticleStats:
        """Đếm bài viết theo trạng thái + tổng views."""
        from app.modules.article.models import Article, ArticleStatus

        # Đếm theo status (chưa soft-delete)
        stmt = (
            select(Article.status, func.count(Article.id))
            .where(Article.deleted_at.is_(None))
            .group_by(Article.status)
        )
        result = await db.execute(stmt)
        status_counts = {status: count for status, count in result.all()}

        published = status_counts.get(ArticleStatus.PUBLISHED, 0)
        draft = status_counts.get(ArticleStatus.DRAFT, 0)
        scheduled = status_counts.get(ArticleStatus.SCHEDULED, 0)
        archived = status_counts.get(ArticleStatus.ARCHIVED, 0)
        total = published + draft + scheduled + archived

        # Đếm thùng rác
        trash_result = await db.execute(
            select(func.count(Article.id)).where(Article.deleted_at.is_not(None))
        )
        trash = trash_result.scalar() or 0

        # Tổng views tất cả bài published (không filter tháng — fix bug logic cũ)
        views_result = await db.execute(
            select(func.coalesce(func.sum(Article.view_count), 0)).where(
                Article.deleted_at.is_(None),
                Article.status == ArticleStatus.PUBLISHED,
            )
        )
        total_views = views_result.scalar() or 0

        return ArticleStats(
            total=total,
            published=published,
            draft=draft,
            scheduled=scheduled,
            archived=archived,
            trash=trash,
            total_views=total_views,
        )

    async def _get_user_stats(self, db: AsyncSession) -> UserStats:
        """Đếm tài khoản theo trạng thái."""
        from app.modules.auth.models import User

        # Active: is_active=True AND deleted_at IS NULL
        active_result = await db.execute(
            select(func.count(User.id)).where(
                User.is_active.is_(True), User.deleted_at.is_(None)
            )
        )
        active = active_result.scalar() or 0

        # Locked: is_active=False AND deleted_at IS NULL
        locked_result = await db.execute(
            select(func.count(User.id)).where(
                User.is_active.is_(False), User.deleted_at.is_(None)
            )
        )
        locked = locked_result.scalar() or 0

        # Deleted: deleted_at IS NOT NULL
        deleted_result = await db.execute(
            select(func.count(User.id)).where(User.deleted_at.is_not(None))
        )
        deleted = deleted_result.scalar() or 0

        return UserStats(
            total=active + locked,
            active=active,
            locked=locked,
            deleted=deleted,
        )

    async def _get_consultation_stats(self, db: AsyncSession) -> ConsultationStats:
        """Đếm đơn tư vấn theo trạng thái."""
        from app.modules.consultation.models import (
            ConsultationLead,
            ConsultationStatus,
        )

        stmt = (
            select(ConsultationLead.status, func.count(ConsultationLead.id))
            .group_by(ConsultationLead.status)
        )
        result = await db.execute(stmt)
        counts = {status: count for status, count in result.all()}

        new = counts.get(ConsultationStatus.NEW, 0)
        contacted = counts.get(ConsultationStatus.CONTACTED, 0)
        consulting = counts.get(ConsultationStatus.CONSULTING, 0)
        completed = counts.get(ConsultationStatus.COMPLETED, 0)
        not_qualified = counts.get(ConsultationStatus.NOT_QUALIFIED, 0)

        return ConsultationStats(
            total=new + contacted + consulting + completed + not_qualified,
            new=new,
            contacted=contacted,
            consulting=consulting,
            completed=completed,
            not_qualified=not_qualified,
        )

    async def _get_content_stats(self, db: AsyncSession) -> ContentStats:
        """Đếm departments, categories, banners, media."""
        from app.modules.department.models import Department
        from app.modules.category.models import Category
        from app.modules.banner.models import Banner
        from app.modules.media.models import MediaItem

        dept_result = await db.execute(
            select(func.count(Department.id)).where(Department.deleted_at.is_(None))
        )
        departments = dept_result.scalar() or 0

        cat_result = await db.execute(
            select(func.count(Category.id)).where(Category.deleted_at.is_(None))
        )
        categories = cat_result.scalar() or 0

        banner_result = await db.execute(
            select(func.count(Banner.id)).where(Banner.deleted_at.is_(None))
        )
        banners = banner_result.scalar() or 0

        # Media: count files + total size
        media_result = await db.execute(
            select(
                func.count(MediaItem.id),
                func.coalesce(func.sum(MediaItem.size), 0),
            ).where(MediaItem.is_folder.is_(False))
        )
        row = media_result.one()
        media_count = row[0] or 0
        media_storage_bytes = row[1] or 0

        return ContentStats(
            departments=departments,
            categories=categories,
            banners=banners,
            media_count=media_count,
            media_storage_bytes=media_storage_bytes,
        )

    async def _get_login_stats(self, db: AsyncSession) -> LoginStats:
        """Thống kê đăng nhập: hôm nay, 7 ngày, thất bại."""
        from app.modules.auth.models import LoginHistory

        now = datetime.now(timezone.utc)
        start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_7_days = start_of_today - timedelta(days=7)

        # Đăng nhập thành công hôm nay
        today_result = await db.execute(
            select(func.count(LoginHistory.id)).where(
                LoginHistory.status == "success",
                LoginHistory.created_at >= start_of_today,
            )
        )
        today = today_result.scalar() or 0

        # Đăng nhập thành công 7 ngày
        week_result = await db.execute(
            select(func.count(LoginHistory.id)).where(
                LoginHistory.status == "success",
                LoginHistory.created_at >= start_of_7_days,
            )
        )
        last_7_days = week_result.scalar() or 0

        # Đăng nhập thất bại hôm nay
        failed_result = await db.execute(
            select(func.count(LoginHistory.id)).where(
                LoginHistory.status == "failed",
                LoginHistory.created_at >= start_of_today,
            )
        )
        failed_today = failed_result.scalar() or 0

        return LoginStats(
            today=today,
            last_7_days=last_7_days,
            failed_today=failed_today,
        )

    async def _get_top_articles(
        self, db: AsyncSession, limit: int = 5
    ) -> list[TopArticleItem]:
        """Top bài viết có nhiều lượt xem nhất."""
        from app.modules.article.models import Article, ArticleStatus, ArticleTranslation
        from app.modules.category.models import CategoryTranslation
        from app.modules.language.models import Language

        # Lấy language_id cho tiếng Việt
        lang_result = await db.execute(
            select(Language.id).where(Language.code == "vi")
        )
        vi_lang_id = lang_result.scalar()

        stmt = (
            select(
                Article.id,
                Article.view_count,
                Article.published_at,
                ArticleTranslation.title,
                CategoryTranslation.name.label("category_name"),
            )
            .join(
                ArticleTranslation,
                (ArticleTranslation.article_id == Article.id)
                & (ArticleTranslation.language_id == vi_lang_id),
                isouter=True,
            )
            .join(
                CategoryTranslation,
                (CategoryTranslation.category_id == Article.category_id)
                & (CategoryTranslation.language_id == vi_lang_id),
                isouter=True,
            )
            .where(
                Article.deleted_at.is_(None),
                Article.status == ArticleStatus.PUBLISHED,
            )
            .order_by(Article.view_count.desc())
            .limit(limit)
        )

        result = await db.execute(stmt)
        rows = result.all()

        return [
            TopArticleItem(
                id=str(row.id),
                title=row.title or "Untitled",
                view_count=row.view_count,
                published_at=row.published_at,
                category_name=row.category_name,
            )
            for row in rows
        ]

    async def _get_recent_activities(
        self, db: AsyncSession, limit: int = 10
    ) -> list[RecentActivityItem]:
        """Lấy các hoạt động quản trị gần nhất từ audit_logs."""
        from app.modules.audit.models import AuditLog

        stmt = (
            select(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        items = result.scalars().all()

        return [
            RecentActivityItem(
                actor_username=item.actor_username,
                action=item.action,
                target_type=item.target_type,
                created_at=item.created_at,
            )
            for item in items
        ]


dashboard_service = DashboardService()
