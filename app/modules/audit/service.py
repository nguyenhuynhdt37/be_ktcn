import math
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.models import AuditLog
from app.modules.audit.schemas import AuditLogResponse
from app.modules.auth.schemas import UserResponse


async def log_action(
    db: AsyncSession,
    actor: UserResponse,
    action: str,
    target_type: str,
    target_id: uuid.UUID | None = None,
    changes: dict[str, Any] | None = None,
    request: Request | None = None,
) -> None:
    """
    Records an administrative action in the audit log.

    Args:
        db: Database session.
        actor: The authenticated user performing the action.
        action: Action type (e.g. USER_CREATED, ROLE_DELETED).
        target_type: Resource type (e.g. 'user', 'role').
        target_id: UUID of the affected resource.
        changes: JSON diff of before/after values.
        request: FastAPI Request to extract IP and user agent.
    """
    ip_address = None
    user_agent = None
    if request:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

    entry = AuditLog(
        actor_id=actor.id,
        actor_username=actor.username,
        action=action,
        target_type=target_type,
        target_id=target_id,
        changes=changes,
        ip_address=ip_address,
        user_agent=user_agent,
        created_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    # Do not commit here — caller is responsible for committing
    # This allows the audit log to be part of the same transaction
    await db.flush()


async def get_audit_logs(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    action: Optional[str] = None,
    target_type: Optional[str] = None,
    actor_id: Optional[uuid.UUID] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
) -> tuple[list[AuditLogResponse], int, int]:
    """
    Retrieves paginated and filtered audit log entries.
    """
    query = select(AuditLog)

    if action:
        query = query.where(AuditLog.action == action)
    if target_type:
        query = query.where(AuditLog.target_type == target_type)
    if actor_id:
        query = query.where(AuditLog.actor_id == actor_id)
    if from_date:
        query = query.where(AuditLog.created_at >= from_date)
    if to_date:
        query = query.where(AuditLog.created_at <= to_date)

    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    paginated = (
        query.order_by(AuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await db.execute(paginated)
    items = result.scalars().all()
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return [
        AuditLogResponse(
            id=item.id,
            actor_id=item.actor_id,
            actor_username=item.actor_username,
            action=item.action,
            target_type=item.target_type,
            target_id=item.target_id,
            changes=item.changes,
            ip_address=item.ip_address,
            user_agent=item.user_agent,
            created_at=item.created_at,
        )
        for item in items
    ], total, total_pages
