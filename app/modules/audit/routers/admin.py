import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ForbiddenException
from app.modules.audit.schemas import AuditLogListResponse
from app.modules.audit.service import get_audit_logs
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserResponse

admin_router = APIRouter()


@admin_router.get("", response_model=AuditLogListResponse)
async def list_audit_logs(
    page: int = 1,
    page_size: int = 20,
    action: Optional[str] = None,
    target_type: Optional[str] = None,
    actor_id: Optional[uuid.UUID] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AuditLogListResponse:
    """
    Lấy danh sách nhật ký hành động quản trị phân trang.
    Quyền yêu cầu: Admin.
    """
    if not current_user.is_admin:
        raise ForbiddenException(
            message="Chỉ Admin mới có quyền xem nhật ký hoạt động của hệ thống",
            error_code="FORBIDDEN_ACCESS"
        )
    items, total, total_pages = await get_audit_logs(
        db, page, page_size, action, target_type, actor_id, from_date, to_date
    )
    return AuditLogListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
