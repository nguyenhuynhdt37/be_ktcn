import uuid
from typing import Tuple, List, Optional
from datetime import datetime, timezone, timedelta
from fastapi import Request
from sqlalchemy import select, delete, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.exceptions import UnauthorizedException, ForbiddenException, NotFoundException, BadRequestException
from app.core.security import verify_password, hash_password, create_access_token
from app.modules.auth.models import User, RefreshToken, LoginHistory
from app.modules.auth.schemas import (
    UserLogin,
    Token,
    UserCreate,
    UserUpdate,
    ProfileUpdateRequest,
    ActiveDeviceResponse,
    LoginHistoryResponse,
    LoginHistoryItemResponse,
    UserSessionResponse,
    LockUserResponse,
    AnomalyReportResponse,
    AnomalyItem,
)
import hashlib


def hash_token(token: str) -> str:
    """Hash token before storing in database for security"""
    return hashlib.sha256(token.encode()).hexdigest()


class AuthService:
    
    async def authenticate(
        self, db: AsyncSession, credentials: UserLogin, ip_address: str, user_agent: Optional[str]
    ) -> Tuple[Token, str]:
        stmt = select(User).where(User.username == credentials.username)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not verify_password(credentials.password, user.password_hash):
            if user:
                await self._log_login_attempt(db, user.id, ip_address, user_agent, "failed", "Sai mật khẩu")
            raise UnauthorizedException(
                message="Tên đăng nhập hoặc mật khẩu không chính xác",
                error_code="INVALID_CREDENTIALS"
            )

        if not user.is_active:
            await self._log_login_attempt(db, user.id, ip_address, user_agent, "failed", "Tài khoản bị khóa")
            raise ForbiddenException(
                message="Tài khoản đã bị vô hiệu hóa",
                error_code="ACCOUNT_DISABLED"
            )

        # Update last login time
        user.last_login = datetime.now(timezone.utc)
        
        # Log successful login
        await self._log_login_attempt(db, user.id, ip_address, user_agent, "success")

        # Generate tokens
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=str(user.id), expires_delta=access_token_expires
        )
        
        refresh_token = str(uuid.uuid4())
        refresh_token_expires = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        new_rt = RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh_token),
            expires_at=refresh_token_expires,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(new_rt)
        await db.commit()

        return Token(access_token=access_token), refresh_token

    async def _log_login_attempt(
        self, db: AsyncSession, user_id: uuid.UUID, ip_address: str, user_agent: Optional[str], status: str, reason: Optional[str] = None
    ):
        log = LoginHistory(
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            failure_reason=reason
        )
        db.add(log)

    async def rotate_refresh_token(
        self, db: AsyncSession, raw_refresh_token: str, ip_address: str, user_agent: Optional[str]
    ) -> Tuple[Token, str]:
        token_hash = hash_token(raw_refresh_token)
        
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await db.execute(stmt)
        rt = result.scalar_one_or_none()

        if not rt:
            raise UnauthorizedException(message="Token làm mới không tồn tại", error_code="INVALID_REFRESH_TOKEN")

        if rt.is_revoked:
            await self.logout_all(db, rt.user_id)
            raise UnauthorizedException(message="Token đã bị thu hồi", error_code="REVOKED_TOKEN")

        if rt.expires_at < datetime.now(timezone.utc):
            raise UnauthorizedException(message="Token làm mới đã hết hạn", error_code="EXPIRED_REFRESH_TOKEN")

        rt.is_revoked = True
        
        user_stmt = select(User).where(User.id == rt.user_id)
        user_result = await db.execute(user_stmt)
        user = user_result.scalar_one_or_none()

        if not user or not user.is_active:
            raise UnauthorizedException(message="Người dùng không hợp lệ", error_code="INVALID_USER")

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=str(user.id), expires_delta=access_token_expires
        )

        new_raw_refresh_token = str(uuid.uuid4())
        refresh_token_expires = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        new_rt = RefreshToken(
            user_id=user.id,
            token_hash=hash_token(new_raw_refresh_token),
            expires_at=refresh_token_expires,
            ip_address=ip_address,
            user_agent=user_agent,
            parent_token_id=rt.id
        )
        db.add(new_rt)
        await db.commit()

        return Token(access_token=access_token), new_raw_refresh_token

    async def logout(self, db: AsyncSession, raw_refresh_token: str):
        token_hash = hash_token(raw_refresh_token)
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await db.execute(stmt)
        rt = result.scalar_one_or_none()

        if rt and not rt.is_revoked:
            rt.is_revoked = True
            await db.commit()

    async def logout_all(self, db: AsyncSession, user_id: uuid.UUID):
        stmt = select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False
        )
        result = await db.execute(stmt)
        tokens = result.scalars().all()
        for token in tokens:
            token.is_revoked = True
        await db.commit()

    async def list_active_devices(self, db: AsyncSession, user_id: uuid.UUID, current_token_hash: Optional[str] = None) -> List[ActiveDeviceResponse]:
        stmt = select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False,
            RefreshToken.expires_at > datetime.now(timezone.utc)
        ).order_by(desc(RefreshToken.created_at))
        
        result = await db.execute(stmt)
        tokens = result.scalars().all()

        return [
            ActiveDeviceResponse(
                id=t.id,
                ip_address=t.ip_address,
                user_agent=t.user_agent,
                created_at=t.created_at,
                expires_at=t.expires_at,
                is_current=(t.token_hash == current_token_hash) if current_token_hash else False
            )
            for t in tokens
        ]

    async def revoke_device(self, db: AsyncSession, user_id: uuid.UUID, device_id: uuid.UUID):
        stmt = select(RefreshToken).where(
            RefreshToken.id == device_id,
            RefreshToken.user_id == user_id
        )
        result = await db.execute(stmt)
        token = result.scalar_one_or_none()
        
        if not token:
            raise NotFoundException(message="Không tìm thấy thiết bị")
            
        token.is_revoked = True
        await db.commit()

    async def get_users_page(
        self, db: AsyncSession, page: int, page_size: int, search: Optional[str] = None, is_active: Optional[bool] = None
    ):
        query = select(User).where(User.deleted_at == None).options(selectinload(User.avatar))

        if search:
            query = query.where(User.username.ilike(f"%{search}%") | User.email.ilike(f"%{search}%") | User.full_name.ilike(f"%{search}%"))
        
        if is_active is not None:
            query = query.where(User.is_active == is_active)

        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query)

        query = query.order_by(desc(User.created_at)).offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        items = result.scalars().all()

        total_pages = (total + page_size - 1) // page_size
        return items, total, total_pages

    async def create_user(self, db: AsyncSession, payload: UserCreate, current_user):
        stmt = select(User).where((User.username == payload.username) | (User.email == payload.email))
        result = await db.execute(stmt)
        if result.scalars().first():
            raise BadRequestException("Username hoặc email đã tồn tại")

        user = User(
            username=payload.username,
            email=payload.email,
            password_hash=hash_password(payload.password),
            full_name=payload.full_name,
            phone=payload.phone,
            bio=payload.bio,
            title=payload.title,
            avatar_id=payload.avatar_id,
            is_active=payload.is_active,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user, ["avatar"])
        return user

    async def update_user(self, db: AsyncSession, user_id: uuid.UUID, payload: UserUpdate, current_user):
        stmt = select(User).where(User.id == user_id).options(selectinload(User.avatar))
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundException("User không tồn tại")

        update_data = payload.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(user, key, value)

        await db.commit()
        await db.refresh(user, ["avatar"])
        return user

    async def get_user_detail(self, db: AsyncSession, user_id: uuid.UUID):
        stmt = select(User).where(User.id == user_id).options(selectinload(User.avatar))
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundException("User không tồn tại")
        return user

    async def delete_user(self, db: AsyncSession, user_id: uuid.UUID, current_user):
        user = await self.get_user_detail(db, user_id)
        user.deleted_at = datetime.now(timezone.utc)
        user.is_active = False
        await db.commit()

    async def check_email_exists(self, db: AsyncSession, email: str) -> bool:
        stmt = select(func.count(User.id)).where(User.email == email, User.deleted_at == None)
        result = await db.execute(stmt)
        return result.scalar() > 0

    async def check_username_exists(self, db: AsyncSession, username: str) -> bool:
        stmt = select(func.count(User.id)).where(User.username == username, User.deleted_at == None)
        result = await db.execute(stmt)
        return result.scalar() > 0

    async def get_user_sessions(self, db: AsyncSession, user_id: uuid.UUID) -> List[UserSessionResponse]:
        stmt = select(RefreshToken).where(
            RefreshToken.user_id == user_id
        ).order_by(desc(RefreshToken.created_at))
        result = await db.execute(stmt)
        return [
            UserSessionResponse(
                id=t.id,
                ip_address=t.ip_address,
                user_agent=t.user_agent,
                created_at=t.created_at,
                expires_at=t.expires_at,
                is_revoked=t.is_revoked
            ) for t in result.scalars().all()
        ]

    async def get_login_history(
        self, db: AsyncSession, user_id: uuid.UUID, page: int, page_size: int, status: Optional[str]
    ) -> LoginHistoryResponse:
        query = select(LoginHistory).where(LoginHistory.user_id == user_id)
        if status:
            query = query.where(LoginHistory.status == status)

        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query)

        query = query.order_by(desc(LoginHistory.created_at)).offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        items = result.scalars().all()

        total_pages = (total + page_size - 1) // page_size
        return LoginHistoryResponse(
            items=[LoginHistoryItemResponse.model_validate(i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    async def revoke_user_session(self, db: AsyncSession, user_id: uuid.UUID, session_id: uuid.UUID):
        stmt = select(RefreshToken).where(RefreshToken.id == session_id, RefreshToken.user_id == user_id)
        result = await db.execute(stmt)
        token = result.scalar_one_or_none()
        if not token:
            raise NotFoundException("Session không tồn tại")
        token.is_revoked = True
        await db.commit()

    async def revoke_all_user_sessions(self, db: AsyncSession, user_id: uuid.UUID) -> int:
        stmt = select(RefreshToken).where(RefreshToken.user_id == user_id, RefreshToken.is_revoked == False)
        result = await db.execute(stmt)
        tokens = result.scalars().all()
        for t in tokens:
            t.is_revoked = True
        await db.commit()
        return len(tokens)

    async def lock_user(self, db: AsyncSession, user_id: uuid.UUID) -> LockUserResponse:
        user = await self.get_user_detail(db, user_id)
        user.is_active = False
        await self.revoke_all_user_sessions(db, user_id)
        await db.commit()
        return LockUserResponse(success=True, message="Đã khóa tài khoản", user_id=user_id, is_active=False)

    async def unlock_user(self, db: AsyncSession, user_id: uuid.UUID) -> LockUserResponse:
        user = await self.get_user_detail(db, user_id)
        user.is_active = True
        await db.commit()
        return LockUserResponse(success=True, message="Đã mở khóa tài khoản", user_id=user_id, is_active=True)

    async def get_anomaly_report(self, db: AsyncSession, user_id: uuid.UUID) -> AnomalyReportResponse:
        return AnomalyReportResponse(
            user_id=user_id,
            risk_level="SAFE",
            anomalies=[],
            active_session_count=0,
            failed_login_count_24h=0,
            generated_at=datetime.now(timezone.utc)
        )

    # ─── Profile Management ──────────────────────────────────────────────────

    async def get_my_profile(self, db: AsyncSession, user_id: uuid.UUID) -> User:
        """
        Lấy thông tin hồ sơ chi tiết của user hiện tại (bao gồm avatar relation).
        """
        stmt = select(User).where(User.id == user_id).options(selectinload(User.avatar))
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundException("Không tìm thấy người dùng")
        return user

    async def update_my_profile(
        self, db: AsyncSession, user_id: uuid.UUID, payload: ProfileUpdateRequest
    ) -> User:
        """
        Cập nhật thông tin cá nhân. Chỉ cho phép sửa: full_name, phone, bio, title, avatar_id.
        KHÔNG cho phép đổi username, email, is_active.
        """
        stmt = select(User).where(User.id == user_id).options(selectinload(User.avatar))
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundException("Không tìm thấy người dùng")

        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)

        await db.commit()
        await db.refresh(user, ["avatar"])
        return user

    async def change_password(
        self, db: AsyncSession, user_id: uuid.UUID, current_password: str, new_password: str
    ) -> None:
        """
        Đổi mật khẩu: xác minh mật khẩu cũ, hash và lưu mật khẩu mới.
        Cập nhật password_changed_at.
        """
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundException("Không tìm thấy người dùng")

        if not verify_password(current_password, user.password_hash):
            raise BadRequestException("Mật khẩu hiện tại không chính xác")

        if current_password == new_password:
            raise BadRequestException("Mật khẩu mới không được trùng với mật khẩu hiện tại")

        user.password_hash = hash_password(new_password)
        user.password_changed_at = datetime.now(timezone.utc)
        await db.commit()
