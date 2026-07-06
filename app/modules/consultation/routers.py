import csv
import io
import uuid

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserResponse
from app.modules.consultation.models import ConsultationRequestType, ConsultationStatus
from app.modules.consultation.schemas import (
    ConsultationAdminResponse,
    ConsultationCreate,
    ConsultationCreatedResponse,
    ConsultationPaginationResponse,
    ConsultationUpdate,
)
from app.modules.consultation.service import consultation_service

portal_router = APIRouter()
admin_router = APIRouter()


@portal_router.post(
    "",
    response_model=ConsultationCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_consultation(
    payload: ConsultationCreate,
    db: AsyncSession = Depends(get_db),
) -> ConsultationCreatedResponse:
    lead = await consultation_service.create(db, payload)
    return ConsultationCreatedResponse(
        id=lead.id,
        reference_code=lead.reference_code,
        status=lead.status,
        created_at=lead.created_at,
    )


@admin_router.get("", response_model=ConsultationPaginationResponse)
async def list_consultations(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, max_length=120),
    status_filter: ConsultationStatus | None = Query(default=None, alias="status"),
    request_type: ConsultationRequestType | None = Query(default=None),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConsultationPaginationResponse:
    del current_user
    items, total = await consultation_service.list_admin(
        db,
        page=page,
        page_size=page_size,
        search=search,
        status=status_filter,
        request_type=request_type,
    )
    total_pages = (total + page_size - 1) // page_size if total else 0
    return ConsultationPaginationResponse(
        items=[ConsultationAdminResponse.model_validate(item) for item in items],
        page=page,
        page_size=page_size,
        total_items=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
    )


@admin_router.get("/export")
async def export_consultations(
    search: str | None = Query(default=None, max_length=120),
    status_filter: ConsultationStatus | None = Query(default=None, alias="status"),
    request_type: ConsultationRequestType | None = Query(default=None),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    del current_user
    items, _ = await consultation_service.list_admin(
        db,
        page=1,
        page_size=10_000,
        search=search,
        status=status_filter,
        request_type=request_type,
    )
    output = io.StringIO()
    output.write("\ufeff")
    writer = csv.writer(output)
    writer.writerow(
        [
            "Mã yêu cầu",
            "Họ và tên",
            "Số điện thoại",
            "Email",
            "Ngành quan tâm",
            "Nhu cầu",
            "Trạng thái",
            "Ngày gửi",
            "Nội dung",
            "Lịch sử ghi chú",
        ]
    )
    for item in items:
        writer.writerow(
            [
                item.reference_code,
                item.full_name,
                item.phone,
                item.email,
                item.interested_major,
                item.request_type.value,
                item.status.value,
                item.created_at.isoformat(),
                item.message or "",
                item.admin_notes or "",
            ]
        )
    return Response(
        content=output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": (
                'attachment; filename="danh-sach-tu-van-tuyen-sinh.csv"'
            )
        },
    )


@admin_router.patch("/{lead_id}", response_model=ConsultationAdminResponse)
async def update_consultation(
    lead_id: uuid.UUID,
    payload: ConsultationUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConsultationAdminResponse:
    item = await consultation_service.update_admin(
        db,
        lead_id=lead_id,
        payload=payload,
        actor_name=current_user.full_name or current_user.username,
    )
    return ConsultationAdminResponse.model_validate(item)
