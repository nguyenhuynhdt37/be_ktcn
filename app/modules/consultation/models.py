import enum
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Enum, ForeignKey, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.models.base import BaseModel


class ConsultationStatus(str, enum.Enum):
    """
    Trạng thái xử lý yêu cầu tư vấn tuyển sinh.
    """
    PENDING = "PENDING"          # Chờ xử lý
    PROCESSING = "PROCESSING"    # Đang xử lý
    COMPLETED = "COMPLETED"      # Đã hoàn thành
    CANCELLED = "CANCELLED"      # Đã hủy


class Consultation(BaseModel):
    """
    Model lưu trữ thông tin các yêu cầu tư vấn tuyển sinh (Leads).
    """
    __tablename__ = "consultations"

    request_code: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    fullname: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    status: Mapped[ConsultationStatus] = mapped_column(
        Enum(ConsultationStatus, name="consultation_status", native_enum=True),
        default=ConsultationStatus.PENDING,
        nullable=False,
        index=True
    )
    
    assigned_to: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Relationships
    assignee: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_to])
