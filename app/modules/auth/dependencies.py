import uuid
from typing import Optional
import jwt
from fastapi import Cookie, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.config import settings


def resolve_avatar_url(avatar_url: Optional[str]) -> Optional[str]:
    if not avatar_url or avatar_url == "http://example.com/avatar.jpg":
        return None
    if avatar_url.startswith("http://") or avatar_url.startswith("https://") or avatar_url.startswith("data:"):
        return avatar_url
    
    protocol = "https" if settings.MINIO_SECURE else "http"
    prefix = "/api/v1/portal/media/file/"
    if avatar_url.startswith(prefix):
        avatar_url = avatar_url.replace(prefix, "")
    return f"{protocol}://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET}/{avatar_url}"

from app.core.database import get_db
from app.core.exceptions import UnauthorizedException
from app.core.security import decode_access_token
from app.modules.auth.models import User
from app.modules.auth.schemas import TokenPayload, UserResponse

reusable_oauth2_optional = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    access_token: Optional[str] = Cookie(None),
    http_auth: Optional[HTTPAuthorizationCredentials] = Depends(reusable_oauth2_optional),
    db: AsyncSession = Depends(get_db),
) -> UserResponse | None:
    """
    Optional user authentication. Returns UserResponse if a valid token is provided in cookie or header,
    otherwise returns None without raising UnauthorizedException.
    """
    token = access_token
    if not token and http_auth:
        token = http_auth.credentials

    if not token:
        return None
        
    try:
        payload = decode_access_token(token)
        token_data = TokenPayload(**payload)
        if token_data.sub is None:
            return None
        user_uuid = uuid.UUID(token_data.sub)
    except Exception:
        return None

    stmt = select(User).where(User.id == user_uuid).options(joinedload(User.avatar))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        return None

    roles = ["super_admin"] if user.username == "superadmin" else ["admin"]
    avatar_url = resolve_avatar_url(user.avatar.object_key if user.avatar else user.avatar_url)

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        avatar_url=avatar_url,
        roles=roles,
        is_active=user.is_active,
    )


async def get_current_user(
    access_token: Optional[str] = Cookie(None),
    http_auth: Optional[HTTPAuthorizationCredentials] = Depends(reusable_oauth2_optional),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Retrieves the currently authenticated user by decoding the JWT access token from cookies (or header)
    and querying the PostgreSQL database.
    """
    token = access_token
    if not token and http_auth:
        token = http_auth.credentials

    if not token:
        raise UnauthorizedException(
            message="Chưa đăng nhập hoặc phiên làm việc hết hạn",
            error_code="MISSING_ACCESS_TOKEN"
        )

    try:
        payload = decode_access_token(token)
        token_data = TokenPayload(**payload)
        if token_data.sub is None:
            raise UnauthorizedException(
                message="Access token thiếu thông tin định danh",
                error_code="INVALID_ACCESS_TOKEN"
            )
    except jwt.ExpiredSignatureError as err:
        raise UnauthorizedException(
            message="Access token đã hết hạn",
            error_code="EXPIRED_ACCESS_TOKEN"
        ) from err
    except (jwt.PyJWTError, ValueError) as err:
        raise UnauthorizedException(
            message="Access token không hợp lệ",
            error_code="INVALID_ACCESS_TOKEN"
        ) from err

    try:
        user_uuid = uuid.UUID(token_data.sub)
    except ValueError as err:
        raise UnauthorizedException(
            message="Định dạng định danh token không hợp lệ",
            error_code="INVALID_ACCESS_TOKEN"
        ) from err

    stmt = select(User).where(User.id == user_uuid).options(joinedload(User.avatar))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise UnauthorizedException(
            message="Không tìm thấy người dùng",
            error_code="USER_NOT_FOUND"
        )
    if not user.is_active:
        raise UnauthorizedException(
            message="Tài khoản người dùng đã bị khóa hoặc chưa kích hoạt",
            error_code="INACTIVE_USER"
        )

    roles = ["super_admin"] if user.username == "superadmin" else (["admin"] if user.is_admin else ["member"])
    avatar_url = resolve_avatar_url(user.avatar.object_key if user.avatar else user.avatar_url)

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        avatar_url=avatar_url,
        roles=roles,
        is_active=user.is_active,
        is_admin=user.is_admin,
    )
