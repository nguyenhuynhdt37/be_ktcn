import uuid
from typing import List, Optional
from fastapi import APIRouter, Cookie, Depends, Request, Response
import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import TooManyRequestsException, UnauthorizedException
from app.core.security import decode_access_token
from app.modules.auth.dependencies import get_current_user, has_permission, require_superadmin
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
    UserAccessOverviewResponse,
    UserSessionResponse,
    RoleResponse,
    RoleCreate,
    RoleUpdate,
    RoleDetailResponse,
    RoleListItemResponse,
    PermissionResponse,
    RoleAssignPermissions,
    UserCreate,
    UserUpdate,
    UserDetailResponse,
)

from app.modules.auth.service import AuthService, hash_token

router = APIRouter(prefix="/auth", tags=["Authentication"])
users_router = APIRouter(prefix="/users", tags=["Users"])
auth_service = AuthService()


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """
    Helper to set the secure, HttpOnly refresh token cookie.
    Sets expiration for 8 days matching the database expiration.
    """
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
    Log in with username and password to get a short-lived access token in body
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
        is_active=True, role="user", permissions=[],
    )
    await log_action(db, login_actor, "AUTH_LOGIN", "session", None, {"ip": ip_address}, request)
    await db.commit()

    set_refresh_cookie(response, raw_refresh_token)
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

    set_refresh_cookie(response, new_raw_refresh_token)
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
    Clears the HttpOnly cookie.
    """
    if refresh_token:
        await auth_service.logout(db, refresh_token)

    await log_action(db, current_user, "AUTH_LOGOUT", "session", None, None, request)
    await db.commit()

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
    role_code: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: UserResponse = Depends(has_permission("user.view")),
    db: AsyncSession = Depends(get_db),
) -> UserListResponse:
    """
    Get a paginated, filtered list of users.
    Protected by RBAC 'user.view' permission.
    """
    items, total, total_pages = await auth_service.get_users_page(
        db,
        page=page,
        page_size=page_size,
        search=search,
        role_code=role_code,
        is_active=is_active,
    )
    
    list_items = []
    for item in items:
        roles_mapped = [
            RoleResponse(id=r.id, name=r.name, code=r.code)
            for r in item.roles
        ]
        
        avatar_url = item.avatar_url
        if item.avatar:
            protocol = "https" if settings.MINIO_SECURE else "http"
            avatar_url = f"{protocol}://{settings.MINIO_ENDPOINT}/{item.avatar.bucket or settings.MINIO_BUCKET}/{item.avatar.object_key}"
            
        list_items.append(
            UserListItemResponse(
                id=item.id,
                username=item.username,
                email=item.email,
                phone=item.phone,
                full_name=item.full_name,
                avatar_url=avatar_url,
                is_active=item.is_active,
                last_login=item.last_login,
                created_at=item.created_at,
                roles=roles_mapped,
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
    current_user: UserResponse = Depends(has_permission("user.create")),
    db: AsyncSession = Depends(get_db),
) -> UserDetailResponse:
    """
    Tạo một tài khoản thành viên mới trong hệ thống.
    Quyền yêu cầu: user.create
    """
    user = await auth_service.create_user(db, payload, current_user)
    await log_action(
        db, current_user, "USER_CREATED", "user", user.id,
        {"username": user.username, "email": user.email, "roles": [r.code for r in user.roles]},
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
    current_user: UserResponse = Depends(has_permission("user.view")),
    db: AsyncSession = Depends(get_db),
) -> UserDetailResponse:
    """
    Lấy thông tin chi tiết một thành viên theo ID.
    Quyền yêu cầu: user.view
    """
    user = await auth_service.get_user_detail(db, user_id)
    return UserDetailResponse.model_validate(user)


@users_router.put("/{user_id}", response_model=UserDetailResponse)
async def update_user(
    request: Request,
    user_id: uuid.UUID,
    payload: UserUpdate,
    current_user: UserResponse = Depends(has_permission("user.update")),
    db: AsyncSession = Depends(get_db),
) -> UserDetailResponse:
    """
    Cập nhật thông tin chi tiết hoặc vai trò của thành viên.
    Quyền yêu cầu: user.update
    """
    changes = {k: v for k, v in payload.model_dump(exclude_none=True).items()}
    if "role_ids" in changes:
        changes["role_ids"] = [str(rid) for rid in changes["role_ids"]]
    user = await auth_service.update_user(db, user_id, payload, current_user)
    await log_action(db, current_user, "USER_UPDATED", "user", user_id, changes, request)
    await db.commit()
    return UserDetailResponse.model_validate(user)


@users_router.delete("/{user_id}")
async def delete_user(
    request: Request,
    user_id: uuid.UUID,
    current_user: UserResponse = Depends(has_permission("user.delete")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Xóa tài khoản thành viên khỏi hệ thống (soft delete).
    Quyền yêu cầu: user.delete
    """
    await auth_service.delete_user(db, user_id, current_user)
    await log_action(db, current_user, "USER_DELETED", "user", user_id, None, request)
    await db.commit()
    return {"success": True}



# ─── Account Activity Endpoints ───────────────────────────────────────────────

@users_router.get("/{user_id}/sessions", response_model=List[UserSessionResponse])
async def get_user_sessions(
    user_id: uuid.UUID,
    current_user: UserResponse = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
) -> List[UserSessionResponse]:
    """
    Lấy danh sách tất cả phiên đăng nhập (còn hạn) của một tài khoản.
    Bao gồm cả phiên đang hoạt động và đã bị thu hồi.
    Yêu cầu quyền: user.view
    """
    return await auth_service.get_user_sessions(db, user_id)


@users_router.get("/{user_id}/login-history", response_model=LoginHistoryResponse)
async def get_login_history(
    user_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    current_user: UserResponse = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
) -> LoginHistoryResponse:
    """
    Lấy lịch sử đăng nhập có phân trang của một tài khoản.
    Có thể lọc theo trạng thái: 'success' hoặc 'failed'.
    Yêu cầu quyền: user.view
    """
    return await auth_service.get_login_history(
        db, user_id, page=page, page_size=page_size, status=status
    )


@users_router.post("/{user_id}/sessions/{session_id}/revoke")
async def revoke_user_session(
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    current_user: UserResponse = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    """
    Thu hồi (đăng xuất từ xa) một phiên đăng nhập cụ thể của người dùng.
    Yêu cầu quyền: user.update
    """
    await auth_service.revoke_user_session(db, user_id, session_id)
    return {"success": True}


@users_router.post("/{user_id}/sessions/revoke-all")
async def revoke_all_user_sessions(
    user_id: uuid.UUID,
    current_user: UserResponse = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    """
    Thu hồi tất cả phiên đăng nhập đang hoạt động của người dùng.
    Yêu cầu quyền: user.update
    """
    revoked_count = await auth_service.revoke_all_user_sessions(db, user_id)
    return {"success": True, "revoked_count": revoked_count}


@users_router.post("/{user_id}/lock", response_model=LockUserResponse)
async def lock_user(
    request: Request,
    user_id: uuid.UUID,
    current_user: UserResponse = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
) -> LockUserResponse:
    """
    Khoá tài khoản người dùng.
    Yêu cầu quyền: user.lock
    """
    result = await auth_service.lock_user(db, user_id)
    await log_action(db, current_user, "USER_LOCKED", "user", user_id, None, request)
    await db.commit()
    return result


@users_router.post("/{user_id}/unlock", response_model=LockUserResponse)
async def unlock_user(
    request: Request,
    user_id: uuid.UUID,
    current_user: UserResponse = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
) -> LockUserResponse:
    """
    Mở khoá tài khoản người dùng.
    Yêu cầu quyền: user.unlock
    """
    result = await auth_service.unlock_user(db, user_id)
    await log_action(db, current_user, "USER_UNLOCKED", "user", user_id, None, request)
    await db.commit()
    return result


@users_router.get("/{user_id}/anomalies", response_model=AnomalyReportResponse)
async def get_anomaly_report(
    user_id: uuid.UUID,
    current_user: UserResponse = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
) -> AnomalyReportResponse:
    """
    Tạo báo cáo phát hiện hành vi bất thường cho một tài khoản.
    Phân tích: brute-force, IP mới, giờ đăng nhập bất thường, quá nhiều phiên.
    Yêu cầu quyền: user.view
    """
    return await auth_service.get_anomaly_report(db, user_id)


@users_router.get("/{user_id}/access-overview", response_model=UserAccessOverviewResponse)
async def get_user_access_overview(
    user_id: uuid.UUID,
    current_user: UserResponse = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
) -> UserAccessOverviewResponse:
    """
    Trả về tổng quan quyền truy cập của một tài khoản:
      - Danh sách vai trò (roles)
      - Toàn bộ mã quyền (permission_codes) được cấp
      - Các tính năng/mục menu mà tài khoản có thể truy cập,
        kèm danh sách quyền cụ thể được cấp cho từng tính năng đó
    Yêu cầu: super_admin
    """
    return await auth_service.get_user_access_overview(db, user_id)


# ─── Roles and Permissions Routers ───────────────────────────────────────────

roles_router = APIRouter()
permissions_router = APIRouter()


@roles_router.get("", response_model=list[RoleListItemResponse])
async def list_roles(
    current_user: UserResponse = Depends(has_permission("role.view")),
    db: AsyncSession = Depends(get_db),
) -> list[RoleListItemResponse]:
    """
    Lấy danh sách các vai trò (roles) trong hệ thống kèm số lượng quyền hạn.
    Quyền yêu cầu: role.view
    """
    return await auth_service.list_roles(db)


@roles_router.get("/{role_id}", response_model=RoleDetailResponse)
async def get_role_detail(
    role_id: uuid.UUID,
    current_user: UserResponse = Depends(has_permission("role.view")),
    db: AsyncSession = Depends(get_db),
) -> RoleDetailResponse:
    """
    Xem chi tiết thông tin và toàn bộ quyền hạn của một vai trò.
    Quyền yêu cầu: role.view
    """
    return await auth_service.get_role_detail(db, role_id)


@roles_router.post("", response_model=RoleDetailResponse)
async def create_role(
    request: Request,
    payload: RoleCreate,
    current_user: UserResponse = Depends(has_permission("role.create")),
    db: AsyncSession = Depends(get_db),
) -> RoleDetailResponse:
    """
    Tạo một vai trò mới.
    Quyền yêu cầu: role.create
    """
    role = await auth_service.create_role(db, payload)
    await log_action(
        db, current_user, "ROLE_CREATED", "role", role.id,
        {"name": role.name, "code": role.code}, request,
    )
    await db.commit()
    return RoleDetailResponse(
        id=role.id,
        name=role.name,
        code=role.code,
        description=role.description,
        permissions=[],
    )


@roles_router.put("/{role_id}", response_model=RoleDetailResponse)
async def update_role(
    request: Request,
    role_id: uuid.UUID,
    payload: RoleUpdate,
    current_user: UserResponse = Depends(has_permission("role.update")),
    db: AsyncSession = Depends(get_db),
) -> RoleDetailResponse:
    """
    Cập nhật thông tin (tên, mô tả) của một vai trò.
    Quyền yêu cầu: role.update
    """
    await auth_service.update_role(db, role_id, payload)
    await log_action(
        db, current_user, "ROLE_UPDATED", "role", role_id,
        payload.model_dump(exclude_none=True), request,
    )
    await db.commit()
    return await auth_service.get_role_detail(db, role_id)


@roles_router.delete("/{role_id}")
async def delete_role(
    request: Request,
    role_id: uuid.UUID,
    current_user: UserResponse = Depends(has_permission("role.delete")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Xóa một vai trò khỏi hệ thống.
    Quyền yêu cầu: role.delete
    """
    await auth_service.delete_role(db, role_id)
    await log_action(db, current_user, "ROLE_DELETED", "role", role_id, None, request)
    await db.commit()
    return {"success": True}


@roles_router.post("/{role_id}/permissions")
async def assign_role_permissions(
    request: Request,
    role_id: uuid.UUID,
    payload: RoleAssignPermissions,
    current_user: UserResponse = Depends(has_permission("role.assign_permission")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Gán danh sách các quyền hạn cho một vai trò.
    Quyền yêu cầu: role.assign_permission
    """
    await auth_service.assign_role_permissions(db, role_id, payload.permission_ids)
    await log_action(
        db, current_user, "ROLE_PERMISSIONS_CHANGED", "role", role_id,
        {"permission_ids": [str(pid) for pid in payload.permission_ids]}, request,
    )
    await db.commit()
    return {"success": True}


@permissions_router.get("", response_model=list[PermissionResponse])
async def list_all_permissions(
    current_user: UserResponse = Depends(has_permission("permission.view")),
    db: AsyncSession = Depends(get_db),
) -> list[PermissionResponse]:
    """
    Lấy danh sách tất cả các quyền hạn (permissions) có sẵn trên hệ thống.
    Quyền yêu cầu: permission.view
    """
    return await auth_service.list_all_permissions(db)

