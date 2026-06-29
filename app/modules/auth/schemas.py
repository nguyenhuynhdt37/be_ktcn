import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.modules.media.schemas import MediaItemResponse


class UserLogin(BaseModel):
    """
    Request payload for user login.
    """
    username: str
    password: str


class Token(BaseModel):
    """
    Response schema returning the generated JWT.
    """
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """
    Schema representing decoded JWT payload.
    """
    sub: str | None = None
    exp: int | None = None


class UserResponse(BaseModel):
    """
    Response schema for authenticated user information.
    """
    id: uuid.UUID
    username: str
    email: str
    is_active: bool = True



class ActiveDeviceResponse(BaseModel):
    """
    Response schema representing an active user device session.
    """
    id: uuid.UUID
    ip_address: str
    user_agent: str | None = None
    created_at: datetime
    expires_at: datetime
    is_current: bool = False

    model_config = ConfigDict(from_attributes=True)


class UserCompactResponse(BaseModel):
    """
    Compact user info for relationships like author, approver.
    """
    id: uuid.UUID
    username: str
    email: str
    full_name: str
    avatar_url: str | None = None
    
    model_config = ConfigDict(from_attributes=True)


class UserListItemResponse(BaseModel):
    """
    Response schema representing a single user item in a list.
    """
    id: uuid.UUID
    username: str
    email: str
    phone: str | None = None
    full_name: str
    avatar_url: str | None = None
    is_active: bool
    last_login: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    """
    Response schema representing a paginated list of users.
    """
    items: list[UserListItemResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ─── Account Activity Schemas ────────────────────────────────────────────────

class UserSessionResponse(BaseModel):
    """
    Response schema for a single active session belonging to a user.
    """
    id: uuid.UUID
    ip_address: str
    user_agent: str | None = None
    created_at: datetime
    expires_at: datetime
    is_revoked: bool = False

    model_config = ConfigDict(from_attributes=True)


class LoginHistoryItemResponse(BaseModel):
    """
    Response schema for a single login attempt record.
    """
    id: uuid.UUID
    ip_address: str
    user_agent: str | None = None
    status: str                         # "success" | "failed"
    failure_reason: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoginHistoryResponse(BaseModel):
    """
    Paginated response for login history.
    """
    items: list[LoginHistoryItemResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class LockUserResponse(BaseModel):
    """
    Response schema after locking or unlocking a user account.
    """
    success: bool
    message: str
    user_id: uuid.UUID
    is_active: bool


class AnomalyItem(BaseModel):
    """
    A single detected anomaly event.
    """
    type: str           # BRUTE_FORCE | NEW_LOCATION | UNUSUAL_HOUR | MULTI_SESSION
    description: str
    severity: str       # LOW | MEDIUM | HIGH | CRITICAL
    detected_at: datetime


class AnomalyReportResponse(BaseModel):
    """
    Full anomaly report for a user account.
    """
    user_id: uuid.UUID
    risk_level: str                 # SAFE | LOW | MEDIUM | HIGH | CRITICAL
    anomalies: list[AnomalyItem]
    active_session_count: int
    failed_login_count_24h: int
    generated_at: datetime


class UserCreate(BaseModel):
    """
    Request payload for creating a new user account.
    """
    username: str = Field(..., min_length=3, max_length=50, description="Tên đăng nhập")
    email: str = Field(..., min_length=5, max_length=255, description="Địa chỉ email")
    password: str = Field(..., min_length=6, max_length=100, description="Mật khẩu")
    full_name: str = Field(..., min_length=1, max_length=100, description="Họ và tên")
    phone: str | None = Field(default=None, max_length=20, description="Số điện thoại")
    bio: str | None = Field(default=None, description="Mô tả bản thân")
    title: str | None = Field(default=None, max_length=100, description="Chức danh")
    avatar_id: uuid.UUID | None = Field(default=None, description="ID ảnh đại diện")
    is_active: bool = Field(default=True, description="Trạng thái hoạt động")


class UserUpdate(BaseModel):
    """
    Request payload for updating an existing user account.
    """
    full_name: str | None = Field(default=None, min_length=1, max_length=100, description="Họ và tên")
    phone: str | None = Field(default=None, max_length=20, description="Số điện thoại")
    bio: str | None = Field(default=None, description="Mô tả bản thân")
    title: str | None = Field(default=None, max_length=100, description="Chức danh")
    avatar_id: uuid.UUID | None = Field(default=None, description="ID ảnh đại diện")
    is_active: bool | None = Field(default=None, description="Trạng thái hoạt động")


class UserDetailResponse(BaseModel):
    """
    Detailed response schema for a user account.
    """
    id: uuid.UUID
    username: str
    email: str
    phone: str | None
    full_name: str
    bio: str | None
    title: str | None
    avatar_id: uuid.UUID | None
    avatar: MediaItemResponse | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
