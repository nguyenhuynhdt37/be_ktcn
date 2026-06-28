import uuid
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.core.security import decode_access_token
from app.modules.auth.models import User, UserRole, RolePermission, Permission
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

    # Query user with selectinload to eagerly load roles relationship
    stmt = (
        select(User)
        .where(User.id == user_uuid)
        .options(selectinload(User.roles))
    )
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

    role_code = user.roles[0].code if user.roles else "user"

    # Query all permission codes mapped to user roles
    if role_code == "super_admin":
        perm_stmt = select(Permission.code)
        perm_result = await db.execute(perm_stmt)
        permissions = list(perm_result.scalars().all())
    else:
        perm_stmt = (
            select(Permission.code)
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .join(UserRole, RolePermission.role_id == UserRole.role_id)
            .where(UserRole.user_id == user.id)
        )
        perm_result = await db.execute(perm_stmt)
        permissions = list(perm_result.scalars().all())

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        is_active=user.is_active,
        role=role_code,
        permissions=permissions,
    )



def has_permission(required_permission: str):
    """
    Dependency creator that checks if the authenticated user has the specified permission.
    Super Admins automatically bypass permission checks.
    """
    async def dependency(
        http_auth: HTTPAuthorizationCredentials = Depends(reusable_oauth2),
        db: AsyncSession = Depends(get_db),
    ) -> UserResponse:
        current_user = await get_current_user(http_auth, db)
        
        # Bypass permissions for Super Admin
        if current_user.role == "super_admin":
            return current_user

        # Query to verify if any role assigned to the user has the required permission code
        stmt = (
            select(func.count(UserRole.user_id))
            .join(RolePermission, UserRole.role_id == RolePermission.role_id)
            .join(Permission, RolePermission.permission_id == Permission.id)
            .where(UserRole.user_id == current_user.id)
            .where(Permission.code == required_permission)
        )
        
        result = await db.execute(stmt)
        count = result.scalar() or 0
        
        if count == 0:
            raise ForbiddenException(
                message=f"Bạn không có quyền thực hiện hành động này ({required_permission})",
                error_code="FORBIDDEN_ACCESS"
            )
            
        return current_user

    return dependency


async def require_superadmin(
    http_auth: HTTPAuthorizationCredentials = Depends(reusable_oauth2),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Dependency that restricts access exclusively to Super Administrators.
    Any authenticated user without the 'super_admin' role will receive a 403.
    """
    current_user = await get_current_user(http_auth, db)

    if current_user.role != "super_admin":
        raise ForbiddenException(
            message="Chức năng này chỉ dành cho Super Admin",
            error_code="SUPERADMIN_REQUIRED",
        )

    return current_user
