import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Float, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.common.models.base import BaseModel


class AIRequestLog(BaseModel):
    """
    Model lưu trữ nhật ký cuộc gọi AI phục vụ thống kê chi phí và lịch sử.
    """
    __tablename__ = "ai_request_logs"

    # Thông tin người dùng thực hiện (xác thực Admin, nullable nếu hệ thống tự chạy)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Chi tiết cuộc gọi
    model: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Đo lường token và chi phí
    tokens_prompt: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tokens_completion: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Hiệu năng & Trạng thái
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # SUCCESS, FAILED
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
