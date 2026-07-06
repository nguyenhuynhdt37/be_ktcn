import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from app.modules.auth.models import User
from app.modules.consultation.models import (
    ConsultationLead,
    ConsultationRequestType,
    ConsultationStatus,
)
from app.modules.consultation.schemas import ConsultationCreate, ConsultationUpdate
from app.modules.notification.service import notification_service


class ConsultationService:
    async def create(
        self, db: AsyncSession, payload: ConsultationCreate
    ) -> ConsultationLead:
        duplicate_since = datetime.now(UTC) - timedelta(hours=24)
        duplicate_query = select(ConsultationLead.id).where(
            ConsultationLead.phone == payload.phone,
            ConsultationLead.created_at >= duplicate_since,
            ConsultationLead.status.in_(
                [
                    ConsultationStatus.NEW,
                    ConsultationStatus.CONTACTED,
                    ConsultationStatus.CONSULTING,
                ]
            ),
        )
        if (await db.execute(duplicate_query)).scalar_one_or_none():
            raise ConflictException(
                message=(
                    "Số điện thoại này đã gửi yêu cầu trong 24 giờ qua. "
                    "Nhà trường sẽ sớm liên hệ với bạn."
                ),
                error_code="DUPLICATE_CONSULTATION",
            )

        now = datetime.now(UTC)
        lead = ConsultationLead(
            reference_code=f"TV{now:%y%m%d}{secrets.token_hex(2).upper()}",
            full_name=payload.full_name,
            phone=payload.phone,
            email=payload.email,
            interested_major=payload.interested_major,
            request_type=payload.request_type,
            message=payload.message or None,
            consent_given=True,
            consent_at=now,
            status=ConsultationStatus.NEW,
            source="WEBSITE",
        )
        db.add(lead)
        await db.flush()
        recipient_ids = await notification_service.create_consultation_notifications(
            db, lead
        )
        await db.commit()
        await db.refresh(lead)
        await notification_service.publish_consultation_event(recipient_ids, lead)
        return lead

    async def list_admin(
        self,
        db: AsyncSession,
        *,
        page: int,
        page_size: int,
        search: str | None,
        status: ConsultationStatus | None,
        request_type: ConsultationRequestType | None,
    ) -> tuple[list[ConsultationLead], int]:
        filters = []
        if search:
            term = f"%{search.strip()}%"
            filters.append(
                or_(
                    ConsultationLead.full_name.ilike(term),
                    ConsultationLead.phone.ilike(term),
                    ConsultationLead.email.ilike(term),
                    ConsultationLead.reference_code.ilike(term),
                    ConsultationLead.interested_major.ilike(term),
                )
            )
        if status:
            filters.append(ConsultationLead.status == status)
        if request_type:
            filters.append(ConsultationLead.request_type == request_type)

        query = select(ConsultationLead)
        count_query = select(func.count(ConsultationLead.id))
        if filters:
            query = query.where(*filters)
            count_query = count_query.where(*filters)

        total = (await db.execute(count_query)).scalar_one()
        result = await db.execute(
            query.order_by(ConsultationLead.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    async def update_admin(
        self,
        db: AsyncSession,
        *,
        lead_id: uuid.UUID,
        payload: ConsultationUpdate,
        actor_name: str,
    ) -> ConsultationLead:
        lead = await db.get(ConsultationLead, lead_id)
        if not lead:
            raise NotFoundException(
                message="Không tìm thấy yêu cầu tư vấn",
                error_code="CONSULTATION_NOT_FOUND",
            )

        if payload.status is not None:
            lead.status = payload.status

        if "assigned_to_id" in payload.model_fields_set:
            if payload.assigned_to_id is not None:
                assignee = await db.get(User, payload.assigned_to_id)
                if not assignee or not assignee.is_active:
                    raise BadRequestException(
                        message="Người phụ trách không tồn tại hoặc đã bị khóa",
                        error_code="INVALID_ASSIGNEE",
                    )
            lead.assigned_to_id = payload.assigned_to_id

        if payload.note:
            timestamp = datetime.now(UTC).strftime("%d/%m/%Y %H:%M")
            entry = f"[{timestamp}] {actor_name}: {payload.note}"
            lead.admin_notes = (
                f"{lead.admin_notes}\n{entry}" if lead.admin_notes else entry
            )

        await db.commit()
        await db.refresh(lead)
        return lead


consultation_service = ConsultationService()
