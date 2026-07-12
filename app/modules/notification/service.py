import json
import uuid
from datetime import UTC, datetime
from typing import Any

import redis.asyncio as aioredis
from loguru import logger
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User
from app.modules.consultation.models import ConsultationLead
from app.modules.notification.models import Notification, NotificationType
from app.shared import redis


class NotificationService:
    def _localize_field(self, val: str | None, lang: str) -> str | None:
        if not val:
            return val
        try:
            data = json.loads(val)
            if isinstance(data, dict):
                return data.get(lang) or data.get("vi") or val
        except Exception:
            pass
        return val

    async def _resolve_entity_details(
        self,
        db: AsyncSession,
        entity_type: str | None,
        entity_id: uuid.UUID | None,
    ) -> dict | None:
        if not entity_type or not entity_id:
            return None
        try:
            if entity_type in ("consultation_lead", "consultation"):
                from app.modules.consultation.models import ConsultationLead
                stmt = select(ConsultationLead).where(ConsultationLead.id == entity_id)
                res = await db.execute(stmt)
                lead = res.scalar_one_or_none()
                if lead:
                    return {
                        "id": str(lead.id),
                        "reference_code": lead.reference_code,
                        "full_name": lead.full_name,
                        "phone": lead.phone,
                        "email": lead.email,
                        "interested_major": lead.interested_major,
                        "request_type": lead.request_type.value if lead.request_type else None,
                        "message": lead.message,
                        "status": lead.status.value if lead.status else None,
                        "created_at": lead.created_at.isoformat() if lead.created_at else None,
                    }
            elif entity_type == "article":
                from app.modules.article.models import Article, ArticleTranslation
                from sqlalchemy.orm import selectinload
                stmt = select(Article).where(Article.id == entity_id).options(
                    selectinload(Article.translations).selectinload(ArticleTranslation.language)
                )
                res = await db.execute(stmt)
                art = res.scalar_one_or_none()
                if art:
                    title_vi = ""
                    title_en = ""
                    slug_vi = ""
                    slug_en = ""
                    for t in art.translations:
                        if t.language.code == "vi":
                            title_vi = t.title
                            slug_vi = t.slug
                        elif t.language.code == "en":
                            title_en = t.title
                            slug_en = t.slug
                    return {
                        "id": str(art.id),
                        "status": art.status.value if art.status else None,
                        "title_vi": title_vi,
                        "title_en": title_en,
                        "slug_vi": slug_vi,
                        "slug_en": slug_en,
                        "created_at": art.created_at.isoformat() if art.created_at else None,
                    }
        except Exception as e:
            logger.warning("Error resolving notification entity details: {}", e)
        return None

    async def create_consultation_notifications(
        self,
        db: AsyncSession,
        lead: ConsultationLead,
    ) -> list[uuid.UUID]:
        user_ids = list(
            (
                await db.execute(
                    select(User.id).where(
                        User.is_active.is_(True),
                        User.deleted_at.is_(None),
                    )
                )
            )
            .scalars()
            .all()
        )
        
        # Lưu tiêu đề & nội dung dạng JSON song ngữ
        title_dict = {
            "vi": "Có yêu cầu tư vấn tuyển sinh mới",
            "en": "New admissions consultation request"
        }
        message_dict = {
            "vi": f"{lead.full_name} quan tâm ngành {lead.interested_major}",
            "en": f"{lead.full_name} is interested in {lead.interested_major}"
        }
        
        title_json = json.dumps(title_dict, ensure_ascii=False)
        message_json = json.dumps(message_dict, ensure_ascii=False)

        for user_id in user_ids:
            db.add(
                Notification(
                    recipient_id=user_id,
                    type=NotificationType.CONSULTATION_CREATED,
                    title=title_json,
                    message=message_json,
                    related_entity_type="consultation_lead",
                    related_entity_id=lead.id,
                    related_url=f"/consultations?lead={lead.id}",
                )
            )
        return user_ids

    async def publish_consultation_event(
        self,
        recipient_ids: list[uuid.UUID],
        lead: ConsultationLead,
    ) -> None:
        if redis.redis_pool is None:
            return
        client = aioredis.Redis(connection_pool=redis.redis_pool)
        
        title_dict = {
            "vi": "Có yêu cầu tư vấn tuyển sinh mới",
            "en": "New admissions consultation request"
        }
        
        payload = json.dumps(
            {
                "type": NotificationType.CONSULTATION_CREATED.value,
                "title": title_dict,
                "related_url": f"/consultations?lead={lead.id}",
            },
            ensure_ascii=False
        )
        try:
            for recipient_id in recipient_ids:
                await client.publish(f"admin-notifications:{recipient_id}", payload)
        except Exception as exc:
            logger.warning("Could not publish realtime notification: {}", exc)
        finally:
            await client.close()

    async def create_article_notifications(
        self,
        db: AsyncSession,
        article: Any,
    ) -> list[uuid.UUID]:
        user_ids = list(
            (
                await db.execute(
                    select(User.id).where(
                        User.is_active.is_(True),
                        User.deleted_at.is_(None),
                    )
                )
            )
            .scalars()
            .all()
        )
        
        title_vi = ""
        title_en = ""
        for t in article.translations:
            if t.language.code == "vi":
                title_vi = t.title
            elif t.language.code == "en":
                title_en = t.title
                
        if not title_vi:
            title_vi = title_en or "Bài viết mới"
        if not title_en:
            title_en = title_vi
            
        title_dict = {
            "vi": "Bài viết mới đã được xuất bản",
            "en": "New article published"
        }
        message_dict = {
            "vi": f"Bài viết '{title_vi}' đã được đăng công khai.",
            "en": f"Article '{title_en}' has been published."
        }
        
        title_json = json.dumps(title_dict, ensure_ascii=False)
        message_json = json.dumps(message_dict, ensure_ascii=False)

        for user_id in user_ids:
            db.add(
                Notification(
                    recipient_id=user_id,
                    type=NotificationType.ACTION_REQUIRED,
                    title=title_json,
                    message=message_json,
                    related_entity_type="article",
                    related_entity_id=article.id,
                    related_url=f"/admin/articles/edit/{article.id}",
                )
            )
        return user_ids

    async def publish_article_event(
        self,
        recipient_ids: list[uuid.UUID],
        article: Any,
    ) -> None:
        if redis.redis_pool is None:
            return
        client = aioredis.Redis(connection_pool=redis.redis_pool)
        
        title_vi = ""
        title_en = ""
        for t in article.translations:
            if t.language.code == "vi":
                title_vi = t.title
            elif t.language.code == "en":
                title_en = t.title
                
        if not title_vi:
            title_vi = title_en or "Bài viết mới"
        if not title_en:
            title_en = title_vi

        payload = json.dumps(
            {
                "type": NotificationType.ACTION_REQUIRED.value,
                "title": {
                    "vi": "Bài viết mới đã được xuất bản",
                    "en": "New article published"
                },
                "message": {
                    "vi": f"Bài viết '{title_vi}' đã được đăng công khai.",
                    "en": f"Article '{title_en}' has been published."
                },
                "related_url": f"/admin/articles/edit/{article.id}",
            },
            ensure_ascii=False
        )
        try:
            for recipient_id in recipient_ids:
                await client.publish(f"admin-notifications:{recipient_id}", payload)
        except Exception as exc:
            logger.warning("Could not publish realtime notification: {}", exc)
        finally:
            await client.close()

    async def list_for_user(
        self,
        db: AsyncSession,
        *,
        recipient_id: uuid.UUID,
        page: int,
        page_size: int,
        unread_only: bool,
        lang: str = "vi",
    ) -> tuple[list[Notification], int, int]:
        filters = [Notification.recipient_id == recipient_id]
        if unread_only:
            filters.append(Notification.read_at.is_(None))

        total = (
            await db.execute(select(func.count(Notification.id)).where(*filters))
        ).scalar_one()
        unread_count = (
            await db.execute(
                select(func.count(Notification.id)).where(
                    Notification.recipient_id == recipient_id,
                    Notification.read_at.is_(None),
                )
            )
        ).scalar_one()
        result = await db.execute(
            select(Notification)
            .where(*filters)
            .order_by(Notification.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list(result.scalars().all())
        
        # Localize fields and resolve entity details
        for item in items:
            db.expunge(item)
            item.title = self._localize_field(item.title, lang)
            item.message = self._localize_field(item.message, lang)
            item.details = await self._resolve_entity_details(db, item.related_entity_type, item.related_entity_id)

        return items, total, unread_count

    async def mark_read(
        self,
        db: AsyncSession,
        *,
        notification_id: uuid.UUID,
        recipient_id: uuid.UUID,
        lang: str = "vi",
    ) -> Notification | None:
        notification = (
            await db.execute(
                select(Notification).where(
                    Notification.id == notification_id,
                    Notification.recipient_id == recipient_id,
                )
            )
        ).scalar_one_or_none()
        if not notification:
            return None
        if notification.read_at is None:
            notification.read_at = datetime.now(UTC)
            await db.commit()
            await db.refresh(notification)
        
        # Localize and resolve before returning
        db.expunge(notification)
        notification.title = self._localize_field(notification.title, lang)
        notification.message = self._localize_field(notification.message, lang)
        notification.details = await self._resolve_entity_details(db, notification.related_entity_type, notification.related_entity_id)
        
        return notification

    async def mark_all_read(
        self,
        db: AsyncSession,
        *,
        recipient_id: uuid.UUID,
    ) -> int:
        result = await db.execute(
            update(Notification)
            .where(
                Notification.recipient_id == recipient_id,
                Notification.read_at.is_(None),
            )
            .values(read_at=datetime.now(UTC))
        )
        await db.commit()
        return result.rowcount or 0


notification_service = NotificationService()
