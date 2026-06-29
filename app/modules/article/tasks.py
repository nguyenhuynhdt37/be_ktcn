from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger
from sqlalchemy import select

from app.core.database import SessionLocal
from app.modules.article.models import Article, ArticleStatus
from app.modules.auth.models import User


async def auto_publish_scheduled_articles() -> None:
    """
    Quét và tự động chuyển các bài viết ở trạng thái SCHEDULED sang PUBLISHED
    khi thời điểm publish_at <= hiện tại.
    """
    async with SessionLocal() as db:
        try:
            now = datetime.now(timezone.utc)
            # 1. Tìm các bài viết SCHEDULED đã đến giờ xuất bản
            stmt = (
                select(Article)
                .where(
                    Article.status == ArticleStatus.SCHEDULED,
                    Article.is_draft == False,
                    Article.publish_at <= now,
                    Article.deleted_at == None
                )
            )
            res = await db.execute(stmt)
            articles = list(res.scalars().all())
            
            if not articles:
                return

            # 2. Lấy user hệ thống (chọn tài khoản superadmin làm đại diện cho hệ thống)
            user_stmt = select(User).where(User.username == "nguyenhuynhdt37@gmail.com")
            user_res = await db.execute(user_stmt)
            system_user = user_res.scalars().first()

            from app.modules.audit.service import log_action

            # 3. Cập nhật từng bài viết và ghi nhận audit log
            for article in articles:
                previous_status = article.status.value
                article.status = ArticleStatus.PUBLISHED
                article.published_at = now
                article.last_edited_at = now
                db.add(article)
                
                if system_user:
                    # Ghi nhận audit log hành động tự động xuất bản
                    await log_action(
                        db,
                        system_user,
                        "ARTICLE_AUTO_PUBLISHED",
                        "article",
                        article.id,
                        {"title": article.title, "previous_status": previous_status, "scheduler": True}
                    )
            
            await db.commit()
            logger.info(f"[Scheduler] Đã tự động xuất bản thành công {len(articles)} bài viết lên lịch.")
        except Exception as ex:
            await db.rollback()
            logger.error(f"[Scheduler] Lỗi trong quá trình tự động xuất bản bài viết: {str(ex)}")


async def start_article_scheduler_task() -> None:
    """
    Khởi chạy scheduler quản lý các tác vụ của module Article.
    """
    scheduler = AsyncIOScheduler()
    # Thêm job chạy định kỳ mỗi 1 phút (60 giây)
    scheduler.add_job(auto_publish_scheduled_articles, "interval", minutes=1)
    scheduler.start()
    logger.info("[Scheduler] Đã khởi động APScheduler cho module Article thành công (quét mỗi 1 phút).")
