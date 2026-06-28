import hashlib
import math
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestException, ConflictException, NotFoundException, UnauthorizedException
from app.core.security import create_access_token, verify_password, hash_password
from app.modules.auth.models import Feature, FeaturePermission, LoginHistory, Permission, RefreshToken, Role, RolePermission, User, UserRole
from app.modules.media.models import MediaItem
from app.modules.auth.schemas import (
    ActiveDeviceResponse,
    AnomalyItem,
    AnomalyReportResponse,
    AccessibleFeatureItem,
    GrantedPermissionItem,
    LockUserResponse,
    LoginHistoryItemResponse,
    LoginHistoryResponse,
    Token,
    UserAccessOverviewResponse,
    UserLogin,
    UserSessionResponse,
    RoleCreate,
    RoleUpdate,
    RoleDetailResponse,
    RoleListItemResponse,
    PermissionResponse,
    UserCreate,
    UserUpdate,
    UserResponse,
)


def hash_token(token: str) -> str:
    """
    Computes the SHA256 hex digest of a refresh token.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class AuthService:
    """
    Authentication Service managing logins, session tokens, rotation breach detection,
    account activity monitoring, and anomaly detection.
    """

    # ─── Authentication ───────────────────────────────────────────────────────

    async def authenticate(
        self,
        db: AsyncSession,
        credentials: UserLogin,
        ip_address: str,
        user_agent: Optional[str] = None,
    ) -> tuple[Token, str]:
        """
        Authenticates a user, logs the attempt, creates a new session,
        and returns the access token along with the raw refresh token.
        """
        stmt = select(User).where(User.username == credentials.username).options(
            selectinload(User.roles)
        )
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        # If user not found or password incorrect, log failure and reject
        if not user or not verify_password(credentials.password, user.password_hash):
            if user:
                history = LoginHistory(
                    user_id=user.id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    status="failed",
                    failure_reason="incorrect_credentials",
                )
                db.add(history)
                await db.commit()
            raise UnauthorizedException(
                message="Tên đăng nhập hoặc mật khẩu không chính xác",
                error_code="INCORRECT_CREDENTIALS"
            )

        # Check if user is active or soft-deleted
        if not user.is_active or user.deleted_at is not None:
            reason = "deleted_user" if user.deleted_at else "inactive_user"
            history = LoginHistory(
                user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent,
                status="failed",
                failure_reason=reason,
            )
            db.add(history)
            await db.commit()
            raise UnauthorizedException(
                message="Tài khoản người dùng đã bị khóa hoặc chưa kích hoạt",
                error_code="INACTIVE_USER"
            )

        # Update last login timestamp
        user.last_login = datetime.now(timezone.utc)
        db.add(user)

        # Generate new tokens
        access_token = create_access_token(subject=str(user.id))
        raw_refresh_token = secrets.token_hex(32)
        token_hash = hash_token(raw_refresh_token)

        # Refresh token expiration: 8 days
        expires_at = datetime.now(timezone.utc) + timedelta(days=8)

        refresh_record = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            is_revoked=False,
        )
        db.add(refresh_record)

        history = LoginHistory(
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            status="success",
        )
        db.add(history)
        await db.commit()

        return Token(access_token=access_token), raw_refresh_token

    async def rotate_refresh_token(
        self,
        db: AsyncSession,
        raw_refresh_token: str,
        ip_address: str,
        user_agent: Optional[str] = None,
    ) -> tuple[Token, str]:
        """
        Handles refresh token rotation (RTR).
        Detects breach attempts on reused tokens and revokes all active tokens of the compromised user.
        """
        token_hash = hash_token(raw_refresh_token)

        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await db.execute(stmt)
        token = result.scalar_one_or_none()

        if not token:
            raise UnauthorizedException(
                message="Phiên đăng nhập không hợp lệ",
                error_code="INVALID_SESSION"
            )

        # BREACH DETECTION: reused revoked token → revoke all sessions immediately
        if token.is_revoked:
            stmt_revoke_all = (
                update(RefreshToken)
                .where(RefreshToken.user_id == token.user_id)
                .values(is_revoked=True)
            )
            await db.execute(stmt_revoke_all)
            await db.commit()
            raise UnauthorizedException(
                message="Phát hiện xâm nhập bảo mật: Token đã được sử dụng lại. Tất cả các phiên đã bị thu hồi.",
                error_code="SECURITY_BREACH"
            )

        # Check expiry
        expires_at = token.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            raise UnauthorizedException(
                message="Phiên đăng nhập đã hết hạn",
                error_code="SESSION_EXPIRED"
            )

        token.is_revoked = True
        db.add(token)

        new_access_token = create_access_token(subject=str(token.user_id))
        new_raw_refresh_token = secrets.token_hex(32)
        new_token_hash = hash_token(new_raw_refresh_token)
        new_expires_at = datetime.now(timezone.utc) + timedelta(days=8)

        new_refresh_record = RefreshToken(
            user_id=token.user_id,
            token_hash=new_token_hash,
            expires_at=new_expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            is_revoked=False,
            parent_token_id=token.id,
        )
        db.add(new_refresh_record)
        await db.commit()

        return Token(access_token=new_access_token), new_raw_refresh_token

    async def list_active_devices(
        self, db: AsyncSession, user_id: uuid.UUID, current_token_hash: Optional[str] = None
    ) -> List[ActiveDeviceResponse]:
        """
        Retrieves all active sessions/devices for the specified user (self-service).
        """
        stmt = select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False,
            RefreshToken.expires_at > datetime.now(timezone.utc),
        )
        result = await db.execute(stmt)
        tokens = result.scalars().all()

        return [
            ActiveDeviceResponse(
                id=t.id,
                ip_address=t.ip_address,
                user_agent=t.user_agent,
                created_at=t.created_at,
                expires_at=t.expires_at,
                is_current=(current_token_hash is not None and t.token_hash == current_token_hash),
            )
            for t in tokens
        ]

    async def revoke_device(
        self, db: AsyncSession, user_id: uuid.UUID, device_id: uuid.UUID
    ) -> None:
        """
        Revokes a specific active session (self-service).
        """
        stmt = select(RefreshToken).where(
            RefreshToken.id == device_id, RefreshToken.user_id == user_id
        )
        result = await db.execute(stmt)
        token = result.scalar_one_or_none()

        if token:
            token.is_revoked = True
            db.add(token)
            await db.commit()

    async def logout(self, db: AsyncSession, raw_refresh_token: str) -> None:
        """
        Revokes the active refresh token matching the provided session.
        """
        token_hash = hash_token(raw_refresh_token)
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await db.execute(stmt)
        token = result.scalar_one_or_none()

        if token:
            token.is_revoked = True
            db.add(token)
            await db.commit()

    async def logout_all(self, db: AsyncSession, user_id: uuid.UUID) -> None:
        """
        Revokes all active sessions for the specified user (self-service).
        """
        stmt_revoke_all = (
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked == False,
                RefreshToken.expires_at > datetime.now(timezone.utc),
            )
            .values(is_revoked=True)
        )
        await db.execute(stmt_revoke_all)
        await db.commit()

    # ─── User Management ──────────────────────────────────────────────────────

    async def get_users_page(
        self,
        db: AsyncSession,
        page: int,
        page_size: int,
        search: Optional[str] = None,
        role_code: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[List[User], int, int]:
        """
        Retrieves a paginated, filtered list of users with eagerly loaded roles.
        """
        from app.modules.auth.models import Role

        query = select(User).where(User.deleted_at.is_(None))

        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    User.username.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                    User.full_name.ilike(search_pattern),
                )
            )

        if is_active is not None:
            query = query.where(User.is_active == is_active)

        if role_code:
            query = query.where(User.roles.any(Role.code == role_code))

        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        paginated_query = (
            query.options(selectinload(User.roles), selectinload(User.avatar))
            .order_by(User.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await db.execute(paginated_query)
        items = result.scalars().all()

        total_pages = math.ceil(total / page_size) if total > 0 else 0

        return list(items), total, total_pages

    async def check_email_exists(self, db: AsyncSession, email: str) -> bool:
        """
        Checks if a user with the given email exists in the database.
        """
        stmt = select(User).where(User.email == email)
        res = await db.execute(stmt)
        return res.scalar_one_or_none() is not None

    async def check_username_exists(self, db: AsyncSession, username: str) -> bool:
        """
        Checks if a user with the given username exists in the database.
        """
        stmt = select(User).where(User.username == username)
        res = await db.execute(stmt)
        return res.scalar_one_or_none() is not None

    async def create_user(
        self, db: AsyncSession, payload: UserCreate, current_user: UserResponse
    ) -> User:
        """
        Creates a new user account with production details, avatar, and roles.
        Protects super_admin role from unauthorized assignment.
        """
        # 1. Check duplicate username
        stmt = select(User).where(User.username == payload.username)
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            raise ConflictException(
                message="Tên đăng nhập đã tồn tại trong hệ thống",
                error_code="USERNAME_DUPLICATE",
            )

        # 2. Check duplicate email
        stmt = select(User).where(User.email == payload.email)
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            raise ConflictException(
                message="Địa chỉ email đã tồn tại trong hệ thống",
                error_code="EMAIL_DUPLICATE",
            )

        # 3. Validate avatar_id if provided
        if payload.avatar_id:
            stmt = select(MediaItem).where(MediaItem.id == payload.avatar_id, MediaItem.is_folder == False)
            res = await db.execute(stmt)
            if not res.scalar_one_or_none():
                raise BadRequestException(
                    message="Tệp ảnh đại diện không tồn tại",
                    error_code="AVATAR_NOT_FOUND",
                )

        # 4. Fetch and validate roles
        roles_list = []
        if payload.role_ids:
            stmt = select(Role).where(Role.id.in_(payload.role_ids))
            res = await db.execute(stmt)
            roles_list = list(res.scalars().all())
            if len(roles_list) != len(payload.role_ids):
                raise BadRequestException(
                    message="Một số vai trò được gán không hợp lệ",
                    error_code="INVALID_ROLES_ASSIGNED",
                )

            # Check privilege escalation
            is_caller_superadmin = (current_user.role == "super_admin")
            has_sa_role = any(r.code == "super_admin" for r in roles_list)
            if has_sa_role and not is_caller_superadmin:
                raise BadRequestException(
                    message="Không có quyền gán vai trò quản trị tối cao (Super Admin)",
                    error_code="SUPERADMIN_ASSIGNMENT_DENIED",
                )

        # 5. Create user
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
            roles=roles_list,
        )
        db.add(user)
        await db.commit()
        return await self.get_user_detail(db, user.id)

    async def get_user_detail(self, db: AsyncSession, user_id: uuid.UUID) -> User:
        """
        Retrieves detailed user profile, eagerly loading roles and avatar metadata.
        """
        stmt = (
            select(User)
            .where(User.id == user_id, User.deleted_at.is_(None))
            .options(selectinload(User.roles), selectinload(User.avatar))
        )
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()
        if not user:
            raise NotFoundException(
                message="Người dùng không tồn tại",
                error_code="USER_NOT_FOUND",
            )
        return user

    async def update_user(
        self, db: AsyncSession, user_id: uuid.UUID, payload: UserUpdate, current_user: UserResponse
    ) -> User:
        """
        Updates an existing user profile and roles list.
        Prevents privilege escalation and protects super_admin.
        """
        user = await self.get_user_detail(db, user_id)
        is_caller_superadmin = (current_user.role == "super_admin")

        # 1. Validate avatar_id if updated
        if payload.avatar_id is not None:
            if payload.avatar_id:
                stmt = select(MediaItem).where(MediaItem.id == payload.avatar_id, MediaItem.is_folder == False)
                res = await db.execute(stmt)
                if not res.scalar_one_or_none():
                    raise BadRequestException(
                        message="Tệp ảnh đại diện không tồn tại",
                        error_code="AVATAR_NOT_FOUND",
                    )
            user.avatar_id = payload.avatar_id

        # 2. Update basic fields
        if payload.full_name is not None:
            user.full_name = payload.full_name
        if payload.phone is not None:
            user.phone = payload.phone
        if payload.bio is not None:
            user.bio = payload.bio
        if payload.title is not None:
            user.title = payload.title
        if payload.is_active is not None:
            # Prevent normal users from changing active status of super_admin
            is_target_superadmin = any(r.code == "super_admin" for r in user.roles)
            if is_target_superadmin and not is_caller_superadmin:
                raise BadRequestException(
                    message="Không thể thay đổi trạng thái của vai trò quản trị tối cao",
                    error_code="SUPERADMIN_ROLE_PROTECTED",
                )
            user.is_active = payload.is_active

        # 3. Update roles if provided
        if payload.role_ids is not None:
            is_target_superadmin = any(r.code == "super_admin" for r in user.roles)
            
            # If the user is currently super_admin and caller is not super_admin -> block modifying roles
            if is_target_superadmin and not is_caller_superadmin:
                raise BadRequestException(
                    message="Không có quyền thay đổi vai trò của người quản trị tối cao",
                    error_code="SUPERADMIN_ROLE_PROTECTED",
                )

            stmt = select(Role).where(Role.id.in_(payload.role_ids))
            res = await db.execute(stmt)
            new_roles = list(res.scalars().all())
            if len(new_roles) != len(payload.role_ids):
                raise BadRequestException(
                    message="Một số vai trò được gán không hợp lệ",
                    error_code="INVALID_ROLES_ASSIGNED",
                )

            # Check if caller is trying to add or remove super_admin role
            has_sa_in_new = any(r.code == "super_admin" for r in new_roles)
            if (has_sa_in_new or is_target_superadmin) and not is_caller_superadmin:
                # If they try to set it or if it changes and they are not SA
                if has_sa_in_new != is_target_superadmin:
                    raise BadRequestException(
                        message="Không có quyền gán/gỡ vai trò quản trị tối cao (Super Admin)",
                        error_code="SUPERADMIN_ASSIGNMENT_DENIED",
                    )

            user.roles = new_roles

        db.add(user)
        await db.commit()
        # Reload with relationships
        return await self.get_user_detail(db, user_id)

    async def delete_user(self, db: AsyncSession, user_id: uuid.UUID, current_user: UserResponse) -> None:
        """
        Deletes a user account.
        Prevents self-deletion and super_admin deletion.
        """
        if user_id == current_user.id:
            raise BadRequestException(
                message="Không thể tự xóa tài khoản của chính mình",
                error_code="SELF_DELETION_DENIED",
            )

        user = await self.get_user_detail(db, user_id)
        is_target_superadmin = any(r.code == "super_admin" for r in user.roles)
        if is_target_superadmin:
            raise BadRequestException(
                message="Không thể xóa tài khoản của người quản trị tối cao (Super Admin)",
                error_code="SUPERADMIN_DELETION_DENIED",
            )

        user.deleted_at = datetime.now(timezone.utc)
        await db.commit()

    # ─── Account Activity (Admin) ─────────────────────────────────────────────

    async def get_user_sessions(
        self, db: AsyncSession, target_user_id: uuid.UUID
    ) -> List[UserSessionResponse]:
        """
        Retrieves all non-expired sessions (active and revoked) for a target user.
        Used by admins to audit account activity.
        """
        stmt = (
            select(RefreshToken)
            .where(
                RefreshToken.user_id == target_user_id,
                RefreshToken.expires_at > datetime.now(timezone.utc),
            )
            .order_by(RefreshToken.created_at.desc())
        )
        result = await db.execute(stmt)
        tokens = result.scalars().all()

        return [
            UserSessionResponse(
                id=t.id,
                ip_address=t.ip_address,
                user_agent=t.user_agent,
                created_at=t.created_at,
                expires_at=t.expires_at,
                is_revoked=t.is_revoked,
            )
            for t in tokens
        ]

    async def get_login_history(
        self,
        db: AsyncSession,
        target_user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
    ) -> LoginHistoryResponse:
        """
        Retrieves paginated login history for a target user.
        Optionally filtered by status ('success' or 'failed').
        """
        query = select(LoginHistory).where(LoginHistory.user_id == target_user_id)

        if status:
            query = query.where(LoginHistory.status == status)

        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        paginated = (
            query.order_by(LoginHistory.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await db.execute(paginated)
        items = result.scalars().all()

        total_pages = math.ceil(total / page_size) if total > 0 else 0

        return LoginHistoryResponse(
            items=[
                LoginHistoryItemResponse(
                    id=h.id,
                    ip_address=h.ip_address,
                    user_agent=h.user_agent,
                    status=h.status,
                    failure_reason=h.failure_reason,
                    created_at=h.created_at,
                )
                for h in items
            ],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def revoke_user_session(
        self,
        db: AsyncSession,
        target_user_id: uuid.UUID,
        session_id: uuid.UUID,
    ) -> None:
        """
        Revokes a specific session belonging to the target user.
        Raises NotFoundException if session is not found or belongs to a different user.
        """
        stmt = select(RefreshToken).where(
            RefreshToken.id == session_id,
            RefreshToken.user_id == target_user_id,
        )
        result = await db.execute(stmt)
        token = result.scalar_one_or_none()

        if not token:
            raise NotFoundException(
                message="Phiên đăng nhập không tồn tại hoặc không thuộc người dùng này",
                error_code="SESSION_NOT_FOUND",
            )

        token.is_revoked = True
        db.add(token)
        await db.commit()

    async def revoke_all_user_sessions(
        self, db: AsyncSession, target_user_id: uuid.UUID
    ) -> int:
        """
        Revokes all active sessions for the target user.
        Returns the number of sessions revoked.
        """
        count_stmt = select(func.count()).where(
            RefreshToken.user_id == target_user_id,
            RefreshToken.is_revoked == False,
            RefreshToken.expires_at > datetime.now(timezone.utc),
        )
        count_result = await db.execute(count_stmt)
        revoked_count = count_result.scalar() or 0

        stmt = (
            update(RefreshToken)
            .where(
                RefreshToken.user_id == target_user_id,
                RefreshToken.is_revoked == False,
                RefreshToken.expires_at > datetime.now(timezone.utc),
            )
            .values(is_revoked=True)
        )
        await db.execute(stmt)
        await db.commit()
        return revoked_count

    async def lock_user(
        self, db: AsyncSession, target_user_id: uuid.UUID
    ) -> LockUserResponse:
        """
        Locks a user account (sets is_active = False) and revokes all active sessions.
        Raises NotFoundException if user is not found.
        """
        stmt = select(User).where(User.id == target_user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundException(
                message="Không tìm thấy người dùng",
                error_code="USER_NOT_FOUND",
            )

        user.is_active = False
        db.add(user)

        revoke_stmt = (
            update(RefreshToken)
            .where(
                RefreshToken.user_id == target_user_id,
                RefreshToken.is_revoked == False,
            )
            .values(is_revoked=True)
        )
        await db.execute(revoke_stmt)
        await db.commit()

        return LockUserResponse(
            success=True,
            message=f"Tài khoản {user.username} đã bị khoá và tất cả phiên đăng nhập đã bị thu hồi",
            user_id=user.id,
            is_active=False,
        )

    async def unlock_user(
        self, db: AsyncSession, target_user_id: uuid.UUID
    ) -> LockUserResponse:
        """
        Unlocks a user account (sets is_active = True).
        Raises NotFoundException if user is not found.
        """
        stmt = select(User).where(User.id == target_user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundException(
                message="Không tìm thấy người dùng",
                error_code="USER_NOT_FOUND",
            )

        user.is_active = True
        db.add(user)
        await db.commit()

        return LockUserResponse(
            success=True,
            message=f"Tài khoản {user.username} đã được mở khoá thành công",
            user_id=user.id,
            is_active=True,
        )

    async def get_anomaly_report(
        self, db: AsyncSession, target_user_id: uuid.UUID
    ) -> AnomalyReportResponse:
        """
        Analyses login history and active sessions to produce an anomaly report.

        Detection rules:
          - BRUTE_FORCE:   ≥5 failed logins within any 15-minute window in the last 24h
          - NEW_LOCATION:  Successful login from an IP never seen before
          - UNUSUAL_HOUR:  Successful login outside 06:00–23:00 VN time (UTC+7)
          - MULTI_SESSION: More than 5 simultaneous active sessions
        """
        now = datetime.now(timezone.utc)
        since_24h = now - timedelta(hours=24)
        vn_offset = timedelta(hours=7)
        anomalies: list[AnomalyItem] = []

        # ── Fetch data ──────────────────────────────────────────────────────
        hist_stmt = (
            select(LoginHistory)
            .where(LoginHistory.user_id == target_user_id)
            .order_by(LoginHistory.created_at.desc())
            .limit(500)
        )
        hist_result = await db.execute(hist_stmt)
        history: list[LoginHistory] = list(hist_result.scalars().all())

        session_stmt = select(RefreshToken).where(
            RefreshToken.user_id == target_user_id,
            RefreshToken.is_revoked == False,
            RefreshToken.expires_at > now,
        )
        session_result = await db.execute(session_stmt)
        active_sessions: list[RefreshToken] = list(session_result.scalars().all())

        # ── BRUTE_FORCE ─────────────────────────────────────────────────────
        recent_failures = [
            h for h in history
            if h.status == "failed"
            and h.created_at.replace(tzinfo=timezone.utc) >= since_24h
        ]
        failed_24h = len(recent_failures)

        if recent_failures:
            failures_sorted = sorted(recent_failures, key=lambda h: h.created_at)
            window = timedelta(minutes=15)
            max_in_window = 0
            window_start_event = None
            for i, f in enumerate(failures_sorted):
                t_i = f.created_at.replace(tzinfo=timezone.utc)
                count_in_window = sum(
                    1 for g in failures_sorted[i:]
                    if g.created_at.replace(tzinfo=timezone.utc) - t_i <= window
                )
                if count_in_window > max_in_window:
                    max_in_window = count_in_window
                    window_start_event = f

            if max_in_window >= 5:
                anomalies.append(AnomalyItem(
                    type="BRUTE_FORCE",
                    description=(
                        f"Phát hiện {max_in_window} lần đăng nhập thất bại trong vòng 15 phút "
                        f"(bắt đầu từ {window_start_event.created_at.strftime('%H:%M %d/%m/%Y')})"
                    ),
                    severity="CRITICAL",
                    detected_at=now,
                ))

        # ── NEW_LOCATION ─────────────────────────────────────────────────────
        new_location_events = [
            h for h in history
            if h.status == "success"
            and h.created_at.replace(tzinfo=timezone.utc) >= since_24h
            and sum(
                1 for prev in history
                if prev.status == "success"
                and prev.ip_address == h.ip_address
                and prev.created_at < h.created_at
            ) == 0
        ]
        if new_location_events:
            ips = list({e.ip_address for e in new_location_events})
            anomalies.append(AnomalyItem(
                type="NEW_LOCATION",
                description=(
                    f"Đăng nhập thành công từ {len(ips)} địa chỉ IP mới chưa từng xuất hiện: "
                    f"{', '.join(ips[:3])}{'...' if len(ips) > 3 else ''}"
                ),
                severity="HIGH",
                detected_at=now,
            ))

        # ── UNUSUAL_HOUR ─────────────────────────────────────────────────────
        unusual_logins = [
            h for h in history
            if h.status == "success"
            and h.created_at.replace(tzinfo=timezone.utc) >= since_24h
            and not (6 <= (h.created_at.replace(tzinfo=timezone.utc) + vn_offset).hour < 23)
        ]
        if unusual_logins:
            hours = [
                (h.created_at.replace(tzinfo=timezone.utc) + vn_offset).strftime("%H:%M")
                for h in unusual_logins[:3]
            ]
            anomalies.append(AnomalyItem(
                type="UNUSUAL_HOUR",
                description=(
                    f"Phát hiện {len(unusual_logins)} lần đăng nhập ngoài giờ bình thường (06:00–23:00 VN) "
                    f"trong 24h qua: {', '.join(hours)}"
                ),
                severity="MEDIUM",
                detected_at=now,
            ))

        # ── MULTI_SESSION ─────────────────────────────────────────────────────
        session_count = len(active_sessions)
        if session_count > 5:
            anomalies.append(AnomalyItem(
                type="MULTI_SESSION",
                description=(
                    f"Tài khoản đang có {session_count} phiên đăng nhập đồng thời "
                    f"(ngưỡng bất thường: >5 phiên)"
                ),
                severity="LOW",
                detected_at=now,
            ))

        # ── Risk level aggregation ────────────────────────────────────────────
        severity_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
        risk_map = {4: "CRITICAL", 3: "HIGH", 2: "MEDIUM", 1: "LOW", 0: "SAFE"}
        max_severity = max(
            (severity_order.get(a.severity, 0) for a in anomalies), default=0
        )
        risk_level = risk_map[max_severity]

        return AnomalyReportResponse(
            user_id=target_user_id,
            risk_level=risk_level,
            anomalies=anomalies,
            active_session_count=session_count,
            failed_login_count_24h=failed_24h,
            generated_at=now,
        )

    async def get_user_access_overview(
        self, db: AsyncSession, target_user_id: uuid.UUID
    ) -> UserAccessOverviewResponse:
        """
        Produces a full access overview for a given user:

        1. Fetch the user with eagerly loaded roles → each role has its permissions.
        2. Collect the union of all permissions granted across roles (deduped by id).
        3. Load all features with their permission lists.
        4. For each feature, intersect its permissions with the user's granted permissions.
           Features with at least one intersecting permission are included.

        Super admin check is handled at the router level (require_superadmin).
        Raises NotFoundException if the target user is not found.
        """
        stmt = (
            select(User)
            .where(User.id == target_user_id)
            .options(
                selectinload(User.roles).selectinload(Role.permissions)
            )
        )
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundException(
                message="Không tìm thấy người dùng",
                error_code="USER_NOT_FOUND",
            )

        # ── Step 1: Gather all permissions granted via roles ───────────────────
        granted_perm_map: dict[uuid.UUID, Permission] = {}
        for role in user.roles:
            for perm in role.permissions:
                granted_perm_map[perm.id] = perm

        granted_perm_ids: set[uuid.UUID] = set(granted_perm_map.keys())

        # ── Step 2: Load all visible features with their permissions ──────────
        feat_stmt = (
            select(Feature)
            .options(selectinload(Feature.permissions))
            .order_by(Feature.sort_order)
        )
        feat_result = await db.execute(feat_stmt)
        all_features: list[Feature] = list(feat_result.scalars().all())

        # ── Step 3: Intersect feature permissions with user's granted set ──────
        accessible_features: list[AccessibleFeatureItem] = []
        for feature in all_features:
            feature_perm_ids = {p.id for p in feature.permissions}
            intersection = feature_perm_ids & granted_perm_ids

            if not intersection:
                continue  # User has no access to this feature

            granted_for_feature = [
                GrantedPermissionItem(
                    id=granted_perm_map[pid].id,
                    name=granted_perm_map[pid].name,
                    code=granted_perm_map[pid].code,
                    module=granted_perm_map[pid].module,
                    action=granted_perm_map[pid].action,
                    description=granted_perm_map[pid].description,
                )
                for pid in sorted(intersection, key=lambda x: granted_perm_map[x].code)
            ]

            accessible_features.append(
                AccessibleFeatureItem(
                    id=feature.id,
                    name=feature.name,
                    code=feature.code,
                    route=feature.route,
                    icon=feature.icon,
                    sort_order=feature.sort_order,
                    is_visible=feature.is_visible,
                    granted_permissions=granted_for_feature,
                )
            )

        from app.modules.auth.schemas import RoleResponse
        return UserAccessOverviewResponse(
            user_id=user.id,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
            roles=[
                RoleResponse(id=r.id, name=r.name, code=r.code)
                for r in user.roles
            ],
            permission_codes=sorted(p.code for p in granted_perm_map.values()),
            accessible_features=accessible_features,
            total_permissions=len(granted_perm_map),
            total_accessible_features=len(accessible_features),
        )

    # ─── Role & Permission Management Service Methods ────────────────────────

    async def _get_role_or_raise(self, db: AsyncSession, role_id: uuid.UUID) -> Role:
        stmt = select(Role).where(Role.id == role_id)
        result = await db.execute(stmt)
        role = result.scalar_one_or_none()
        if not role:
            raise NotFoundException(
                message="Không tìm thấy vai trò",
                error_code="ROLE_NOT_FOUND",
            )
        return role

    async def list_roles(self, db: AsyncSession) -> list[RoleListItemResponse]:
        """
        Lists all roles along with the count of permissions assigned to each.
        """
        stmt = (
            select(Role)
            .options(selectinload(Role.permissions))
            .order_by(Role.code)
        )
        result = await db.execute(stmt)
        roles = result.scalars().all()
        return [
            RoleListItemResponse(
                id=role.id,
                name=role.name,
                code=role.code,
                description=role.description,
                permissions_count=len(role.permissions),
            )
            for role in roles
        ]

    async def get_role_detail(self, db: AsyncSession, role_id: uuid.UUID) -> RoleDetailResponse:
        """
        Retrieves detailed information of a role including its full permissions list.
        """
        stmt = (
            select(Role)
            .where(Role.id == role_id)
            .options(selectinload(Role.permissions))
        )
        result = await db.execute(stmt)
        role = result.scalar_one_or_none()
        if not role:
            raise NotFoundException(
                message="Không tìm thấy vai trò",
                error_code="ROLE_NOT_FOUND",
            )
        return RoleDetailResponse.model_validate(role)

    async def create_role(self, db: AsyncSession, payload: RoleCreate) -> Role:
        """
        Creates a new security role.
        Throws ConflictException if role code already exists.
        """
        # Check duplicate code
        dup_stmt = select(Role).where(Role.code == payload.code)
        dup_result = await db.execute(dup_stmt)
        if dup_result.scalar_one_or_none():
            raise ConflictException(
                message="Mã vai trò đã tồn tại trong hệ thống",
                error_code="ROLE_CODE_DUPLICATE",
            )

        role = Role(
            name=payload.name,
            code=payload.code,
            description=payload.description,
        )
        db.add(role)
        await db.commit()
        await db.refresh(role)
        return role

    async def update_role(self, db: AsyncSession, role_id: uuid.UUID, payload: RoleUpdate) -> Role:
        """
        Updates an existing role's name and description.
        Protects the super_admin role from modification.
        """
        role = await self._get_role_or_raise(db, role_id)
        if role.code == "super_admin":
            raise BadRequestException(
                message="Không được phép sửa đổi vai trò quản trị tối cao (Super Admin)",
                error_code="SUPERADMIN_ROLE_PROTECTED",
            )

        role.name = payload.name
        role.description = payload.description
        db.add(role)
        await db.commit()
        await db.refresh(role)
        return role

    async def delete_role(self, db: AsyncSession, role_id: uuid.UUID) -> None:
        """
        Deletes a role from the system.
        Protects the 4 fixed system roles (super_admin, admin, editor, author) from deletion.
        Chặn xóa nếu vai trò đang được gán cho bất kỳ người dùng nào.
        """
        role = await self._get_role_or_raise(db, role_id)
        if role.code in {"super_admin", "admin", "editor", "author"}:
            raise BadRequestException(
                message=f"Không được phép xóa vai trò hệ thống cố định ({role.name})",
                error_code="SYSTEM_ROLE_PROTECTED",
            )

        # Check if any user is currently assigned to this role
        user_role_stmt = select(func.count(UserRole.user_id)).where(UserRole.role_id == role_id)
        user_role_result = await db.execute(user_role_stmt)
        user_count = user_role_result.scalar() or 0
        if user_count > 0:
            raise BadRequestException(
                message=f"Không thể xóa vai trò '{role.name}' vì đang có {user_count} người dùng được gán vai trò này. Vui lòng chuyển vai trò của họ trước khi xóa.",
                error_code="ROLE_HAS_ASSIGNED_USERS",
            )

        await db.delete(role)
        await db.commit()

    async def assign_role_permissions(
        self, db: AsyncSession, role_id: uuid.UUID, permission_ids: list[uuid.UUID]
    ) -> None:
        """
        Assigns a list of permissions to a role.
        Protects the super_admin role.
        """
        role = await self._get_role_or_raise(db, role_id)
        if role.code == "super_admin":
            raise BadRequestException(
                message="Không được phép thay đổi quyền hạn của vai trò quản trị tối cao (Super Admin)",
                error_code="SUPERADMIN_ROLE_PROTECTED",
            )

        # 1. Fetch valid permissions matching the ids
        perm_stmt = select(Permission).where(Permission.id.in_(permission_ids))
        perm_result = await db.execute(perm_stmt)
        valid_perms = list(perm_result.scalars().all())

        if len(valid_perms) != len(permission_ids):
            raise BadRequestException(
                message="Một số ID quyền hạn cung cấp không hợp lệ",
                error_code="INVALID_PERMISSIONS_PROVIDED",
            )

        # 2. Reset and assign new permissions list
        # Eager load permissions to avoid lazy loading issues
        stmt = (
            select(Role)
            .where(Role.id == role_id)
            .options(selectinload(Role.permissions))
        )
        result = await db.execute(stmt)
        role_loaded = result.scalar_one()

        role_loaded.permissions = valid_perms
        db.add(role_loaded)
        await db.commit()

    async def list_all_permissions(self, db: AsyncSession) -> list[PermissionResponse]:
        """
        Lists all system permissions available.
        """
        stmt = select(Permission).order_by(Permission.module, Permission.code)
        result = await db.execute(stmt)
        perms = result.scalars().all()
        return [PermissionResponse.model_validate(p) for p in perms]

