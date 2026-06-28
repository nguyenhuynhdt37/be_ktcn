import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ──────────────────────────────────────────────
# AI Settings Schemas
# ──────────────────────────────────────────────

class AISettingCreate(BaseModel):
    """Yêu cầu tạo cấu hình AI mới."""
    provider: str = Field(..., max_length=50, description="Nhà cung cấp (Chỉ hỗ trợ: gemini)")
    setting_type: str = Field(default="text", description="Loại cấu hình (text hoặc embedding)")
    base_url: Optional[str] = Field(default=None, max_length=255, description="URL tùy chỉnh của API")
    api_key: Optional[str] = Field(default=None, description="API Key chưa mã hóa (sẽ được BE mã hóa khi lưu)")
    model: str = Field(..., max_length=100, description="Tên Model (Ví dụ: gemini-2.5-flash hoặc text-embedding-004)")
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, ge=1)
    timeout: int = Field(default=30, ge=1, description="Thời gian chờ tối đa (giây)")
    is_enabled: bool = Field(default=True)
    
    # Budget Limits
    monthly_budget_limit: float = Field(default=50.0000, ge=0.0, description="Ngân sách tối đa hàng tháng (USD)")
    budget_reset_day: int = Field(default=1, ge=1, le=31, description="Ngày tự động reset ngân sách")

    @model_validator(mode="after")
    def validate_provider(self):
        if self.provider.lower() != "gemini":
            raise ValueError("Hệ thống chỉ hỗ trợ Google Gemini. Provider khác không được phép.")
        if self.setting_type.lower() not in ["text", "embedding"]:
            raise ValueError("Hệ thống chỉ hỗ trợ setting_type là 'text' hoặc 'embedding'.")
        return self


class AISettingUpdate(BaseModel):
    """Yêu cầu cập nhật cấu hình AI."""
    setting_type: str = Field(..., description="Cấu hình cần cập nhật (text hoặc embedding)")
    provider: Optional[str] = Field(default=None, max_length=50)
    base_url: Optional[str] = Field(default=None, max_length=255)
    api_key: Optional[str] = Field(default=None, description="Nhập API Key mới để ghi đè (để trống nếu không đổi)")
    model: Optional[str] = Field(default=None, max_length=100)
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    timeout: Optional[int] = Field(default=None, ge=1)
    is_enabled: Optional[bool] = None
    
    # Budget Limits
    monthly_budget_limit: Optional[float] = Field(default=None, ge=0.0)
    budget_reset_day: Optional[int] = Field(default=None, ge=1, le=31)

    @model_validator(mode="after")
    def validate_provider(self) -> "AISettingUpdate":
        if self.provider is not None and self.provider.lower() != "gemini":
            raise ValueError("Hệ thống chỉ hỗ trợ Google Gemini. Provider khác không được phép.")
        if self.setting_type.lower() not in ["text", "embedding"]:
            raise ValueError("Hệ thống chỉ hỗ trợ setting_type là 'text' hoặc 'embedding'.")
        return self


class AISettingResponse(BaseModel):
    """Thông tin trả về của cấu hình AI (Đã ẩn API Key bảo mật)."""
    id: uuid.UUID
    provider: str
    setting_type: str
    base_url: Optional[str] = None
    api_key_masked: Optional[str] = None
    model: str
    temperature: float
    max_tokens: int
    timeout: int
    is_enabled: bool
    is_active: bool
    
    # Budget Limits
    monthly_budget_limit: float
    monthly_spent: float
    budget_reset_day: int
    currency: str
    
    updated_at: datetime
    api_key_encrypted: Optional[str] = Field(default=None, exclude=True)

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        protected_namespaces=()
    )

    @model_validator(mode="after")
    def mask_api_key(self) -> "AISettingResponse":
        """Che API Key để bảo mật dữ liệu trên Admin UI."""
        if self.api_key_encrypted and self.api_key_encrypted.strip():
            self.api_key_masked = "••••••••••••••••"
        else:
            self.api_key_masked = None
        return self


# ──────────────────────────────────────────────
# AI Model Pricing Schemas
# ──────────────────────────────────────────────

class AIModelPricingCreate(BaseModel):
    """Cấu hình đơn giá token của một Model."""
    provider: str = Field(..., max_length=50)
    model_name: str = Field(..., max_length=100)
    input_price_per_1m: float = Field(..., ge=0.0, description="Đơn giá trên 1 triệu Input Tokens (USD)")
    output_price_per_1m: float = Field(..., ge=0.0, description="Đơn giá trên 1 triệu Output Tokens (USD)")

    model_config = ConfigDict(protected_namespaces=())


class AIModelPricingResponse(BaseModel):
    """Phản hồi thông tin đơn giá model."""
    id: uuid.UUID
    provider: str
    model_name: str
    input_price_per_1m: float
    output_price_per_1m: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


# ──────────────────────────────────────────────
# AI Usage Logs Schemas
# ──────────────────────────────────────────────

class AIUsageLogResponse(BaseModel):
    """Nhật ký chi tiết lượt gọi AI."""
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    provider: str
    model: str
    feature: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ──────────────────────────────────────────────
# AI Generation Schemas
# ──────────────────────────────────────────────

class AIGenerateSEORequest(BaseModel):
    """Payload gửi lên từ Frontend yêu cầu AI trợ giúp gợi ý SEO."""
    title: str = Field(..., min_length=1, description="Tên danh mục hoặc Tiêu đề bài viết")
    description: Optional[str] = Field(default=None, description="Mô tả tóm tắt hiện tại (Summary/Excerpt)")
    content: Optional[str] = Field(default=None, description="Nội dung chi tiết (nếu có, VD của Article)")
    category_name: Optional[str] = Field(default=None, description="Tên danh mục cha hoặc chuyên mục liên kết (nếu có)")


class AIGenerateSEOResponse(BaseModel):
    """Kết quả gợi ý SEO sinh ra bởi trợ lý AI (Chỉ dùng để Preview ở client)."""
    seo_title: str = Field(..., description="Tiêu đề SEO gợi ý tối ưu")
    seo_description: str = Field(..., description="Mô tả SEO gợi ý tối ưu (150-160 ký tự)")
    seo_keywords: Optional[str] = Field(default=None, description="Từ khóa SEO gợi ý")


# ──────────────────────────────────────────────
# AI Test Connection Schemas
# ──────────────────────────────────────────────

class AITestConnectionRequest(BaseModel):
    """Payload kiểm tra kết nối AI (nháp hoặc hiện tại)."""
    provider: str = Field(..., max_length=50, description="Chỉ hỗ trợ: gemini")
    setting_type: str = Field(default="text", description="Loại cấu hình kết nối cần test (text hoặc embedding)")
    base_url: Optional[str] = Field(default=None, max_length=255)
    api_key: Optional[str] = Field(default=None, description="Nhập API key để test, hoặc bỏ trống để test key hiện tại đang lưu")
    model: str = Field(..., max_length=100)
    timeout: int = Field(default=10, ge=1, le=30)

    model_config = ConfigDict(protected_namespaces=())

    @model_validator(mode="after")
    def validate_provider(self) -> "AITestConnectionRequest":
        if self.provider.lower() != "gemini":
            raise ValueError("Hệ thống chỉ hỗ trợ Google Gemini. Provider khác không được phép.")
        if self.setting_type.lower() not in ["text", "embedding"]:
            raise ValueError("Hệ thống chỉ hỗ trợ setting_type là 'text' hoặc 'embedding'.")
        return self


class AIDetectedModelResponse(BaseModel):
    """Thông tin model phát hiện được kèm đơn giá tham chiếu."""
    model_name: str
    input_price_per_1m: float
    output_price_per_1m: float


class AITestConnectionResponse(BaseModel):
    """Kết quả phản hồi kiểm tra kết nối AI."""
    success: bool
    message: str
    error_details: Optional[str] = None
    detected_models: Optional[list[AIDetectedModelResponse]] = None


class AISpendingByModelResponse(BaseModel):
    """Thống kê chi tiết chi tiêu của từng Model AI so với hạn mức chung."""
    provider: str
    model: str
    total_spent: float
    percentage_of_limit: float
