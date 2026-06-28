import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.common.models.base import BaseModel


class AISetting(BaseModel):
    """
    Model lưu trữ cấu hình kết nối AI động của hệ thống và giới hạn ngân sách.
    """
    __tablename__ = "ai_settings"

    provider: Mapped[str] = mapped_column(String(50), nullable=False) # openai, gemini, openrouter, ollama...
    base_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    api_key_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    setting_type: Mapped[str] = mapped_column(String(20), default="text", nullable=False) # text, embedding
    
    temperature: Mapped[float] = mapped_column(Float, default=0.2, nullable=False)
    max_tokens: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    timeout: Mapped[int] = mapped_column(Integer, default=30, nullable=False) # tính theo giây
    
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Quản lý giới hạn ngân sách (Spending Limits)
    monthly_budget_limit: Mapped[float] = mapped_column(Numeric(10, 4), default=50.0000, nullable=False)
    monthly_spent: Mapped[float] = mapped_column(Numeric(10, 4), default=0.0000, nullable=False)
    budget_reset_day: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)

    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class AIModelPricing(BaseModel):
    """
    Bảng cấu hình đơn giá Input/Output token của từng model.
    """
    __tablename__ = "ai_model_pricing"

    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    model_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    input_price_per_1m: Mapped[float] = mapped_column(Numeric(10, 4), default=0.0000, nullable=False)
    output_price_per_1m: Mapped[float] = mapped_column(Numeric(10, 4), default=0.0000, nullable=False)


class AIUsageLog(BaseModel):
    """
    Lưu nhật ký chi tiết sử dụng token và chi phí quy đổi của từng user.
    """
    __tablename__ = "ai_usage_logs"

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    feature: Mapped[str] = mapped_column(String(50), nullable=False) # generate_seo, rewrite...
    
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    cost: Mapped[float] = mapped_column(Numeric(12, 6), default=0.000000, nullable=False)
