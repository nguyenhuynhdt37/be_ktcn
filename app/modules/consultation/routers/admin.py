import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Cookie
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import jwt

from app.core.database import get_db
from app.core.exceptions import UnauthorizedException
from app.core.security import decode_access_token
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserResponse, TokenPayload
from app.modules.auth.models import User
from app.modules.consultation.models import ConsultationStatus
from app.modules.consultation.schemas import (
    ConsultationPaginationResponse,
    ConsultationResponse,
    ConsultationUpdate,
)
from app.modules.consultation.service import consultation_service
from app.modules.consultation.sse import sse_manager
from app.modules.audit.service import log_action

router = APIRouter()


async def get_sse_user(
    token: Optional[str] = Query(None),
    access_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Xác thực người dùng cho kết nối SSE (EventSource).
    Hỗ trợ lấy JWT token từ query parameter 'token' hoặc từ cookie 'access_token'.
    """
    final_token = token or access_token
    if not final_token:
        raise UnauthorizedException(
            message="Chưa đăng nhập hoặc token không hợp lệ",
            error_code="UNAUTHORIZED"
        )
    try:
        payload = decode_access_token(final_token)
        token_data = TokenPayload(**payload)
        if token_data.sub is None:
            raise UnauthorizedException(message="Token không hợp lệ", error_code="INVALID_TOKEN")
        
        user_uuid = uuid.UUID(token_data.sub)
        user_db = await db.get(User, user_uuid)
        if not user_db or not user_db.is_active or user_db.deleted_at is not None:
            raise UnauthorizedException(message="Tài khoản không hoạt động", error_code="INACTIVE_USER")
            
        # Lấy roles của user (nếu có)
        from app.modules.auth.dependencies import get_current_user # reuse logic if needed
        # Để đơn giản, map trực tiếp thông tin cần thiết vào UserResponse
        return UserResponse(
            id=user_db.id,
            username=user_db.username,
            email=user_db.email,
            full_name=user_db.full_name,
            avatar_url=user_db.avatar_url,
            roles=[], # Sẽ được bổ sung nếu cần, tạm thời để trống
            is_active=user_db.is_active
        )
    except Exception as err:
        raise UnauthorizedException(
            message="Token không hợp lệ hoặc đã hết hạn",
            error_code="INVALID_TOKEN"
        ) from err


@router.get("", response_model=ConsultationPaginationResponse)
async def list_consultations(
    page: int = Query(default=1, ge=1, description="Chỉ số trang"),
    page_size: int = Query(default=10, ge=1, le=100, description="Số lượng trên mỗi trang"),
    search: Optional[str] = Query(default=None, description="Tìm kiếm theo tên, sđt, email, mã yêu cầu"),
    status: Optional[ConsultationStatus] = Query(default=None, description="Lọc theo trạng thái"),
    sort_by: str = Query(default="created_at", description="Trường sắp xếp"),
    order: str = Query(default="desc", description="Hướng sắp xếp (asc, desc)"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConsultationPaginationResponse:
    """
    Lấy danh sách các yêu cầu tư vấn tuyển sinh phân trang (Yêu cầu đăng nhập).
    """
    allowed_sort_fields = {"fullname", "phone", "email", "request_code", "created_at", "status"}
    if sort_by not in allowed_sort_fields:
        sort_by = "created_at"

    if order.lower() not in {"asc", "desc"}:
        order = "desc"

    items, total = await consultation_service.list_consultations(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        status=status,
        sort_by=sort_by,
        order=order,
    )

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return ConsultationPaginationResponse(
        items=[ConsultationResponse.model_validate(item) for item in items],
        page=page,
        page_size=page_size,
        total_items=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
    )


@router.patch("/{consultation_id}", response_model=ConsultationResponse)
async def update_consultation(
    request: Request,
    consultation_id: uuid.UUID,
    payload: ConsultationUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConsultationResponse:
    """
    Cập nhật trạng thái, nhận xử lý (gán người xử lý) hoặc ghi chú yêu cầu tư vấn.
    """
    consultation = await consultation_service.update_consultation(
        db, consultation_id, payload, current_user.id
    )

    # Log action
    await log_action(
        db,
        current_user,
        "CONSULTATION_UPDATED",
        "consultation",
        consultation.id,
        payload.model_dump(exclude_unset=True),
        request,
    )
    await db.commit()
    return ConsultationResponse.model_validate(consultation)


@router.get("/export")
async def export_consultations_csv(
    search: Optional[str] = Query(default=None),
    status: Optional[ConsultationStatus] = Query(default=None),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """
    Xuất danh sách yêu cầu tư vấn ra file CSV hỗ trợ Excel tiếng Việt.
    """
    csv_data = await consultation_service.export_csv(db, search=search, status=status)
    
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=danh_sach_yeu_cau_tu_van.csv"
        }
    )


@router.get("/events")
async def sse_notifications_stream(
    req: Request,
    current_user: UserResponse = Depends(get_sse_user),
) -> StreamingResponse:
    """
    SSE Endpoint phát thông tin sự kiện realtime (Ví dụ: có lead mới) cho Admin.
    """
    queue = sse_manager.connect()

    async def event_generator():
        try:
            # Gửi tin nhắn chào mừng ban đầu
            yield "data: {\"event\": \"welcome\", \"message\": \"SSE connection established\"}\n\n"
            
            while True:
                # Kiểm tra xem client đã đóng kết nối chưa
                if await req.is_disconnected():
                    break
                
                try:
                    # Đọc từ queue với timeout ngắn để gửi ping giữ kết nối
                    message = await asyncio.wait_for(queue.get(), timeout=20.0)
                    yield message
                    queue.task_done()
                except asyncio.TimeoutError:
                    # Gửi ping giữ kết nối hoạt động
                    yield ": ping\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            sse_manager.disconnect(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no" # Tắt proxy buffering cho Nginx
        }
    )
