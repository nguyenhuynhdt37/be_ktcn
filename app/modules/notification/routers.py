import asyncio
import json
import uuid

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundException
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserResponse
from app.modules.notification.schemas import (
    MarkAllReadResponse,
    NotificationPaginationResponse,
    NotificationResponse,
    UnreadCountResponse,
)
from app.modules.notification.service import notification_service
from app.shared.redis import get_redis

router = APIRouter()


@router.get("", response_model=NotificationPaginationResponse)
async def list_notifications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    unread_only: bool = Query(default=False),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationPaginationResponse:
    items, total, unread_count = await notification_service.list_for_user(
        db,
        recipient_id=current_user.id,
        page=page,
        page_size=page_size,
        unread_only=unread_only,
    )
    total_pages = (total + page_size - 1) // page_size if total else 0
    return NotificationPaginationResponse(
        items=[NotificationResponse.model_validate(item) for item in items],
        page=page,
        page_size=page_size,
        total_items=total,
        total_pages=total_pages,
        unread_count=unread_count,
        has_next=page < total_pages,
        has_previous=page > 1,
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
async def unread_count(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UnreadCountResponse:
    _, _, count = await notification_service.list_for_user(
        db,
        recipient_id=current_user.id,
        page=1,
        page_size=1,
        unread_only=False,
    )
    return UnreadCountResponse(unread_count=count)


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationResponse:
    item = await notification_service.mark_read(
        db,
        notification_id=notification_id,
        recipient_id=current_user.id,
    )
    if not item:
        raise NotFoundException(
            message="Không tìm thấy thông báo",
            error_code="NOTIFICATION_NOT_FOUND",
        )
    return NotificationResponse.model_validate(item)


@router.post("/read-all", response_model=MarkAllReadResponse)
async def mark_all_notifications_read(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MarkAllReadResponse:
    count = await notification_service.mark_all_read(
        db,
        recipient_id=current_user.id,
    )
    return MarkAllReadResponse(updated_count=count)


@router.get("/stream")
async def notification_stream(
    current_user: UserResponse = Depends(get_current_user),
    redis_client: aioredis.Redis = Depends(get_redis),
) -> StreamingResponse:
    async def event_generator():
        pubsub = redis_client.pubsub()
        channel = f"admin-notifications:{current_user.id}"
        await pubsub.subscribe(channel)
        try:
            yield "event: ready\ndata: {}\n\n"
            while True:
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=20,
                )
                if message and message.get("data"):
                    data = message["data"]
                    if not isinstance(data, str):
                        data = json.dumps(data)
                    yield f"event: notification\ndata: {data}\n\n"
                else:
                    yield ": heartbeat\n\n"
                await asyncio.sleep(0.1)
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
