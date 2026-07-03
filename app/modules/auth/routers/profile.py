"""
Admin Profile Management Router.
Prefix: /api/v1/admin/profile
Tất cả endpoint chỉ thao tác trên tài khoản của user đang đăng nhập.
"""
import uuid
from typing import List, Optional

from fastapi import APIRouter, Cookie, Depends, Request
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import (
    UserResponse,
    MyProfileResponse,
    ProfileUpdateRequest,
    ChangePasswordRequest,
    UserSessionResponse,
    LoginHistoryResponse,
)
from app.modules.auth.service import AuthService, hash_token
from app.modules.audit.service import log_action
from app.modules.audit.models import AuditLog
from app.modules.audit.schemas import AuditLogResponse

router = APIRouter()
auth_service = AuthService()


def _resolve_avatar_url(user) -> str | None:
    """Resolve avatar URL từ avatar relation hoặc avatar_url cột."""
    if user.avatar:
        return user.avatar.object_key
    avatar_url = user.avatar_url
    if avatar_url == "http://example.com/avatar.jpg":
        return None
    return avatar_url


def _build_profile_response(user, roles: list[str]) -> MyProfileResponse:
    """Chuyển User entity thành MyProfileResponse."""
    return MyProfileResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        phone=user.phone,
        full_name=user.full_name,
        bio=user.bio,
        title=user.title,
        avatar_url=_resolve_avatar_url(user),
        roles=roles,
        is_active=user.is_active,
        last_login=user.last_login,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.get("", response_model=MyProfileResponse)
async def get_my_profile(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MyProfileResponse:
    """
    Lấy thông tin hồ sơ chi tiết của tài khoản đang đăng nhập.
    """
    user = await auth_service.get_my_profile(db, current_user.id)
    return _build_profile_response(user, current_user.roles)


@router.put("", response_model=MyProfileResponse)
async def update_my_profile(
    request: Request,
    payload: ProfileUpdateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MyProfileResponse:
    """
    Cập nhật hồ sơ cá nhân (full_name, phone, bio, title, avatar_id).
    Không cho phép đổi username, email, is_active.
    """
    changes = {k: v for k, v in payload.model_dump(exclude_unset=True).items()}
    user = await auth_service.update_my_profile(db, current_user.id, payload)
    await log_action(db, current_user, "PROFILE_UPDATED", "user", current_user.id, changes, request)
    await db.commit()
    return _build_profile_response(user, current_user.roles)


@router.put("/password")
async def change_password(
    request: Request,
    payload: ChangePasswordRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Đổi mật khẩu. Yêu cầu nhập đúng mật khẩu hiện tại.
    """
    await auth_service.change_password(
        db, current_user.id, payload.current_password, payload.new_password
    )
    await log_action(db, current_user, "PASSWORD_CHANGED", "user", current_user.id, None, request)
    await db.commit()
    return {"success": True, "message": "Đổi mật khẩu thành công"}


@router.get("/sessions", response_model=List[UserSessionResponse])
async def get_my_sessions(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[UserSessionResponse]:
    """
    Lấy danh sách phiên đăng nhập của tài khoản hiện tại.
    """
    return await auth_service.get_user_sessions(db, current_user.id)


@router.get("/login-history", response_model=LoginHistoryResponse)
async def get_my_login_history(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LoginHistoryResponse:
    """
    Lấy lịch sử đăng nhập của tài khoản hiện tại.
    """
    return await auth_service.get_login_history(
        db, current_user.id, page=page, page_size=page_size, status=status
    )


@router.get("/activity")
async def get_my_activity(
    limit: int = 10,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Lấy nhật ký hoạt động gần đây của tài khoản hiện tại từ bảng audit_logs.
    Mặc định trả 10 bản ghi gần nhất.
    """
    limit = min(limit, 50)  # Giới hạn tối đa 50

    stmt = (
        select(AuditLog)
        .where(AuditLog.actor_id == current_user.id)
        .order_by(desc(AuditLog.created_at))
        .limit(limit)
    )
    result = await db.execute(stmt)
    items = result.scalars().all()

    count_stmt = select(func.count()).select_from(
        select(AuditLog.id).where(AuditLog.actor_id == current_user.id).subquery()
    )
    total = await db.scalar(count_stmt) or 0

    return {
        "items": [
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
        ],
        "total": total,
    }
