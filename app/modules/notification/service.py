import json
import uuid
from datetime import UTC, datetime

import redis.asyncio as aioredis
from loguru import logger
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User
from app.modules.consultation.models import ConsultationLead
from app.modules.notification.models import Notification, NotificationType
from app.shared import redis


class NotificationService:
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
        for user_id in user_ids:
            db.add(
                Notification(
                    recipient_id=user_id,
                    type=NotificationType.CONSULTATION_CREATED,
                    title="Có yêu cầu tư vấn tuyển sinh mới",
                    message=f"{lead.full_name} quan tâm ngành {lead.interested_major}",
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
        payload = json.dumps(
            {
                "type": NotificationType.CONSULTATION_CREATED.value,
                "title": "Có yêu cầu tư vấn tuyển sinh mới",
                "related_url": f"/consultations?lead={lead.id}",
            }
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
        return list(result.scalars().all()), total, unread_count

    async def mark_read(
        self,
        db: AsyncSession,
        *,
        notification_id: uuid.UUID,
        recipient_id: uuid.UUID,
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
