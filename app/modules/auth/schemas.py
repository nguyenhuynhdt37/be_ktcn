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
    role: str = "user"
    permissions: list[str] = []



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


class RoleResponse(BaseModel):
    """
    Response schema representing a role.
    """
    id: uuid.UUID
    name: str
    code: str

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
    roles: list[RoleResponse]


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


# ─── Access Overview Schemas ─────────────────────────────────────────────────

class GrantedPermissionItem(BaseModel):
    """
    A single permission that has been granted to a user through their role(s).
    """
    id: uuid.UUID
    name: str
    code: str
    module: str
    action: str
    description: str | None = None


class AccessibleFeatureItem(BaseModel):
    """
    A feature (menu item) that the user can access, along with
    the specific permissions they have been granted for it.
    """
    id: uuid.UUID
    name: str
    code: str
    route: str | None = None
    icon: str | None = None
    sort_order: int
    is_visible: bool
    granted_permissions: list[GrantedPermissionItem]


class UserAccessOverviewResponse(BaseModel):
    """
    Full access overview for a given user account.
    Shows their roles, all granted permissions, and
    the feature/menu items they can access — grouped with
    which specific permissions apply to each feature.
    """
    user_id: uuid.UUID
    username: str
    full_name: str
    is_active: bool
    roles: list[RoleResponse]
    permission_codes: list[str]
    accessible_features: list[AccessibleFeatureItem]
    total_permissions: int
    total_accessible_features: int


# ─── Role & Permission Management Schemas ────────────────────────────────────

class RoleCreate(BaseModel):
    """
    Request payload for creating a new security role.
    """
    name: str = Field(..., max_length=100, description="Tên vai trò")
    code: str = Field(..., max_length=50, description="Mã vai trò (unique)")
    description: str | None = Field(default=None, description="Mô tả vai trò")


class RoleUpdate(BaseModel):
    """
    Request payload for updating an existing security role.
    """
    name: str = Field(..., max_length=100, description="Tên vai trò mới")
    description: str | None = Field(default=None, description="Mô tả vai trò mới")


class PermissionResponse(BaseModel):
    """
    Response schema representing a single system permission.
    """
    id: uuid.UUID
    name: str
    code: str
    module: str
    action: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)


class RoleDetailResponse(BaseModel):
    """
    Response schema representing detailed role information including all assigned permissions.
    """
    id: uuid.UUID
    name: str
    code: str
    description: str | None = None
    permissions: list[PermissionResponse]

    model_config = ConfigDict(from_attributes=True)


class RoleListItemResponse(BaseModel):
    """
    Response schema for listing roles, including the number of assigned permissions.
    """
    id: uuid.UUID
    name: str
    code: str
    description: str | None = None
    permissions_count: int

    model_config = ConfigDict(from_attributes=True)


class RoleAssignPermissions(BaseModel):
    """
    Request payload for assigning a list of permissions to a role.
    """
    permission_ids: list[uuid.UUID]


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
    role_ids: list[uuid.UUID] = Field(default_factory=list, description="Danh sách ID vai trò")
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
    role_ids: list[uuid.UUID] | None = Field(default=None, description="Danh sách ID vai trò")
    is_active: bool | None = Field(default=None, description="Trạng thái hoạt động")


class UserDetailResponse(BaseModel):
    """
    Detailed response schema for a user account, including roles and avatar metadata.
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
    roles: list[RoleResponse]

    model_config = ConfigDict(from_attributes=True)

