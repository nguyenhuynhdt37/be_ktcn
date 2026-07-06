import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.models.base import BaseModel


class ConsultationRequestType(str, enum.Enum):
    ADMISSION_CONSULTING = "ADMISSION_CONSULTING"
    CAMPUS_VISIT = "CAMPUS_VISIT"
    RECEIVE_MATERIALS = "RECEIVE_MATERIALS"
    APPLICATION_REGISTRATION = "APPLICATION_REGISTRATION"


class ConsultationStatus(str, enum.Enum):
    NEW = "NEW"
    CONTACTED = "CONTACTED"
    CONSULTING = "CONSULTING"
    COMPLETED = "COMPLETED"
    NOT_QUALIFIED = "NOT_QUALIFIED"


class ConsultationLead(BaseModel):
    """A prospective student or parent requesting admissions support."""

    __tablename__ = "consultation_leads"

    reference_code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    interested_major: Mapped[str] = mapped_column(String(255), nullable=False)
    request_type: Mapped[ConsultationRequestType] = mapped_column(
        Enum(ConsultationRequestType, name="consultation_request_type"),
        nullable=False,
    )
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    consent_given: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    consent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="WEBSITE")
    status: Mapped[ConsultationStatus] = mapped_column(
        Enum(ConsultationStatus, name="consultation_status"),
        nullable=False,
        default=ConsultationStatus.NEW,
        index=True,
    )
    assigned_to_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    assigned_to = relationship("User", foreign_keys=[assigned_to_id])

    __table_args__ = (
        Index("idx_consultation_leads_created_at", "created_at"),
        Index("idx_consultation_leads_status_created", "status", "created_at"),
        Index("idx_consultation_leads_phone_created", "phone", "created_at"),
    )
