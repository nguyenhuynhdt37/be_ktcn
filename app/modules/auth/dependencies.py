import uuid
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import UnauthorizedException
from app.core.security import decode_access_token
from app.modules.auth.models import User
from app.modules.auth.schemas import TokenPayload, UserResponse

reusable_oauth2 = HTTPBearer()


async def get_current_user(
    http_auth: HTTPAuthorizationCredentials = Depends(reusable_oauth2),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Retrieves the currently authenticated user by decoding the JWT access token and
    querying the PostgreSQL database.
    """
    token = http_auth.credentials
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

    stmt = select(User).where(User.id == user_uuid)
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

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        is_active=user.is_active,
    )
