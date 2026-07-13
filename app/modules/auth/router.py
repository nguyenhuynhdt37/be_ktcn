import uuid
from typing import List, Optional
from fastapi import APIRouter, Cookie, Depends, Request, Response
import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import TooManyRequestsException, UnauthorizedException, ForbiddenException
from app.core.security import decode_access_token
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.shared.rate_limiter import check_rate_limit
from app.shared.redis import get_redis
from app.modules.audit.service import log_action
from app.modules.auth.schemas import (
    ActiveDeviceResponse,
    AnomalyReportResponse,
    LockUserResponse,
    LoginHistoryResponse,
    Token,
    UserLogin,
    UserResponse,
    UserListResponse,
    UserListItemResponse,
    UserSessionResponse,
    UserCreate,
    UserUpdate,
    UserDetailResponse,
)

from app.modules.auth.service import AuthService, hash_token

router = APIRouter(prefix="/auth", tags=["Authentication"])
users_router = APIRouter(prefix="/users", tags=["Users"])
auth_service = AuthService()


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """
    Helper to set the secure, HttpOnly access and refresh token cookies.
    """
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.ENV == "production",
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.ENV == "production",
        samesite="lax",
        max_age=8 * 24 * 60 * 60,  # 8 days in seconds
        path="/",  # Accessible system-wide
    )


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    response: Response,
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(get_redis),
) -> Token:
    """
    Log in with username and password to get a short-lived access token in HttpOnly cookie
    and a secure refresh token in HttpOnly cookie.
    Rate limited: 5 failed attempts per minute per IP.
    """
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent")

    # Rate limiting check
    rate_key = f"rate_limit:login:{ip_address}"
    allowed, remaining, retry_after = await check_rate_limit(
        redis_client, rate_key, max_attempts=5, window_seconds=60
    )
    if not allowed:
        raise TooManyRequestsException(
            message=f"Quá nhiều lần đăng nhập thất bại. Vui lòng thử lại sau {retry_after} giây.",
            details={"retry_after": retry_after},
        )

    token_data, raw_refresh_token = await auth_service.authenticate(
        db, credentials, ip_address, user_agent
    )

    # Reset rate limit counter on successful login
    await redis_client.delete(rate_key)

    # Audit log: successful login (extract user_id from JWT)
    jwt_payload = decode_access_token(token_data.access_token)
    login_user_id = uuid.UUID(jwt_payload["sub"])
    login_actor = UserResponse(
        id=login_user_id, username=credentials.username, email="",
        is_active=True,
    )
    await log_action(db, login_actor, "AUTH_LOGIN", "session", None, {"ip": ip_address}, request)
    await db.commit()

    set_auth_cookies(response, token_data.access_token, raw_refresh_token)
    return token_data


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: Request,
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db),
) -> Token:
    """
    Acquire a new access token and rotate the refresh token.
    Reads raw refresh token from HttpOnly cookie.
    """
    if not refresh_token:
        raise UnauthorizedException(
            message="Thiếu token làm mới trong cookie",
            error_code="MISSING_REFRESH_TOKEN"
        )

    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent")

    token_data, new_raw_refresh_token = await auth_service.rotate_refresh_token(
        db, refresh_token, ip_address, user_agent
    )

    set_auth_cookies(response, token_data.access_token, new_raw_refresh_token)
    return token_data


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    """
    Logs out the user by revoking the current session's refresh token.
    Clears both access and refresh token cookies.
    """
    if refresh_token:
        await auth_service.logout(db, refresh_token)

    await log_action(db, current_user, "AUTH_LOGOUT", "session", None, None, request)
    await db.commit()

    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")
    return {"success": True}


@router.get("/devices", response_model=List[ActiveDeviceResponse])
async def list_devices(
    refresh_token: Optional[str] = Cookie(None),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ActiveDeviceResponse]:
    """
    List all active devices/sessions for the authenticated user.
    """
    current_token_hash = hash_token(refresh_token) if refresh_token else None
    return await auth_service.list_active_devices(
        db, current_user.id, current_token_hash
    )


@router.post("/devices/{device_id}/revoke")
async def revoke_device(
    request: Request,
    device_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    """
    Terminates a specific device session.
    """
    await auth_service.revoke_device(db, current_user.id, device_id)
    await log_action(db, current_user, "DEVICE_REVOKED", "session", device_id, None, request)
    await db.commit()
    return {"success": True}


@router.post("/logout-all")
async def logout_all_devices(
    request: Request,
    response: Response,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    """
    Logs out from all devices by revoking all active sessions for the current user.
    """
    await auth_service.logout_all(db, current_user.id)
    await log_action(db, current_user, "AUTH_LOGOUT_ALL", "session", None, None, request)
    await db.commit()
    response.delete_cookie(key="refresh_token", path="/")
    return {"success": True}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    """
    Retrieves profile information for the currently authenticated user.
    """
    return current_user


@users_router.get("/check-email")
async def check_email_exists(
    email: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Kiểm tra xem email đã tồn tại trong hệ thống hay chưa.
    Yêu cầu: Đăng nhập
    """
    exists = await auth_service.check_email_exists(db, email)
    return {"exists": exists}


@users_router.get("", response_model=UserListResponse)
async def list_users(
    page: int = 1,
    page_size: int = 10,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserListResponse:
    """
    Get a paginated, filtered list of users.
    """
    items, total, total_pages = await auth_service.get_users_page(
        db,
        page=page,
        page_size=page_size,
        search=search,
        is_active=is_active,
    )
    
    list_items = []
    for item in items:
        avatar_url = item.avatar_url
        prefix = "/api/v1/portal/media/file/"
        if item.avatar:
            avatar_url = f"{prefix}{item.avatar.object_key}"
        elif avatar_url and not avatar_url.startswith(prefix):
            if "files/" in avatar_url:
                object_key = "files/" + avatar_url.split("files/")[-1]
                avatar_url = f"{prefix}{object_key}"
            else:
                avatar_url = f"{prefix}{avatar_url}"
            
        list_items.append(
            UserListItemResponse(
                id=item.id,
                username=item.username,
                email=item.email,
                phone=item.phone,
                full_name=item.full_name,
                avatar_url=avatar_url,
                is_active=item.is_active,
                is_admin=item.is_admin,
                last_login=item.last_login,
                created_at=item.created_at,
            )
        )
        
    return UserListResponse(
        items=list_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@users_router.post("", response_model=UserDetailResponse)
async def create_user(
    request: Request,
    payload: UserCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserDetailResponse:
    """
    Tạo một tài khoản thành viên mới trong hệ thống.
    """
    if not current_user.is_admin:
        raise ForbiddenException(
            message="Chỉ Admin mới có quyền tạo tài khoản thành viên mới",
            error_code="FORBIDDEN_ACCESS"
        )
    user = await auth_service.create_user(db, payload, current_user)
    await log_action(
        db, current_user, "USER_CREATED", "user", user.id,
        {"username": user.username, "email": user.email},
        request,
    )
    await db.commit()
    return UserDetailResponse.model_validate(user)


@users_router.get("/check-username")
async def check_username_exists(
    username: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Kiểm tra xem username đã tồn tại trong hệ thống hay chưa.
    Yêu cầu: Đăng nhập
    """
    exists = await auth_service.check_username_exists(db, username)
    return {"exists": exists}


@users_router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user_detail(
    user_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserDetailResponse:
    """
    Lấy thông tin chi tiết một thành viên theo ID.
    """
    user = await auth_service.get_user_detail(db, user_id)
    return UserDetailResponse.model_validate(user)


@users_router.put("/{user_id}", response_model=UserDetailResponse)
async def update_user(
    request: Request,
    user_id: uuid.UUID,
    payload: UserUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserDetailResponse:
    """
    Cập nhật thông tin chi tiết hoặc vai trò của thành viên.
    """
    if not current_user.is_admin:
        raise ForbiddenException(
            message="Chỉ Admin mới có quyền cập nhật thông tin hoặc cấp lại mật khẩu cho thành viên khác",
            error_code="FORBIDDEN_ACCESS"
        )
    changes = {k: v for k, v in payload.model_dump(exclude_none=True).items()}
    user = await auth_service.update_user(db, user_id, payload, current_user)
    await log_action(db, current_user, "USER_UPDATED", "user", user_id, changes, request)
    await db.commit()
    return UserDetailResponse.model_validate(user)


@users_router.delete("/{user_id}")
async def delete_user(
    request: Request,
    user_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Xóa tài khoản thành viên khỏi hệ thống (soft delete).
    """
    if not current_user.is_admin:
        raise ForbiddenException(
            message="Chỉ Admin mới có quyền xóa tài khoản thành viên",
            error_code="FORBIDDEN_ACCESS"
        )
    await auth_service.delete_user(db, user_id, current_user)
    await log_action(db, current_user, "USER_DELETED", "user", user_id, None, request)
    await db.commit()
    return {"success": True}



# ─── Account Activity Endpoints ───────────────────────────────────────────────

@users_router.get("/{user_id}/sessions", response_model=List[UserSessionResponse])
async def get_user_sessions(
    user_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[UserSessionResponse]:
    """
    Lấy danh sách tất cả phiên đăng nhập (còn hạn) của một tài khoản.
    Bao gồm cả phiên đang hoạt động và đã bị thu hồi.
    """
    return await auth_service.get_user_sessions(db, user_id)


@users_router.get("/{user_id}/login-history", response_model=LoginHistoryResponse)
async def get_login_history(
    user_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LoginHistoryResponse:
    """
    Lấy lịch sử đăng nhập có phân trang của một tài khoản.
    Có thể lọc theo trạng thái: 'success' hoặc 'failed'.
    """
    return await auth_service.get_login_history(
        db, user_id, page=page, page_size=page_size, status=status
    )


@users_router.post("/{user_id}/sessions/{session_id}/revoke")
async def revoke_user_session(
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    """
    Thu hồi (đăng xuất từ xa) một phiên đăng nhập cụ thể của người dùng.
    """
    await auth_service.revoke_user_session(db, user_id, session_id)
    return {"success": True}


@users_router.post("/{user_id}/sessions/revoke-all")
async def revoke_all_user_sessions(
    user_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    """
    Thu hồi tất cả phiên đăng nhập đang hoạt động của người dùng.
    """
    revoked_count = await auth_service.revoke_all_user_sessions(db, user_id)
    return {"success": True, "revoked_count": revoked_count}


@users_router.post("/{user_id}/lock", response_model=LockUserResponse)
async def lock_user(
    request: Request,
    user_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LockUserResponse:
    """
    Khoá tài khoản người dùng.
    """
    result = await auth_service.lock_user(db, user_id)
    await log_action(db, current_user, "USER_LOCKED", "user", user_id, None, request)
    await db.commit()
    return result


@users_router.post("/{user_id}/unlock", response_model=LockUserResponse)
async def unlock_user(
    request: Request,
    user_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LockUserResponse:
    """
    Mở khoá tài khoản người dùng.
    """
    result = await auth_service.unlock_user(db, user_id)
    await log_action(db, current_user, "USER_UNLOCKED", "user", user_id, None, request)
    await db.commit()
    return result


@users_router.get("/{user_id}/anomalies", response_model=AnomalyReportResponse)
async def get_anomaly_report(
    user_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AnomalyReportResponse:
    """
    Tạo báo cáo phát hiện hành vi bất thường cho một tài khoản.
    Phân tích: brute-force, IP mới, giờ đăng nhập bất thường, quá nhiều phiên.
    """
    return await auth_service.get_anomaly_report(db, user_id)
