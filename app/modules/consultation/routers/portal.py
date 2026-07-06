from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.consultation.schemas import ConsultationCreate, ConsultationResponse
from app.modules.consultation.service import consultation_service

router = APIRouter()


@router.post("", response_model=ConsultationResponse, status_code=201)
async def create_consultation_request(
    request: Request,
    payload: ConsultationCreate,
    db: AsyncSession = Depends(get_db),
) -> ConsultationResponse:
    """
    Gửi yêu cầu tư vấn tuyển sinh mới từ client portal.
    """
    consultation = await consultation_service.create_consultation(db, payload)
    await db.commit()
    return ConsultationResponse.model_validate(consultation)
