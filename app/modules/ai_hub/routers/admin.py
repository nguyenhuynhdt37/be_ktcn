import time
import uuid
import httpx
from pathlib import Path
from loguru import logger
from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserResponse
from app.modules.ai_hub.schemas import (
    AISettingsUpdateRequest,
    AISettingsResponse,
    AIPlaygroundRequest,
    AIPlaygroundResponse,
    AILogListResponse,
    AISpendResponse,
    AIEmbeddingPlaygroundRequest,
    AIEmbeddingPlaygroundResponse,
)
from app.modules.ai_hub.service import ai_hub_service
from app.shared.ai.config import (
    get_active_model,
    save_active_model,
    get_active_embedding_model,
    save_active_embedding_model,
)

ai_hub_router = APIRouter()


def get_embedding_priority_list() -> list[str]:
    return ["embedding-model (Google gemini-embedding-2)"]


@ai_hub_router.get(
    "/models",
    response_model=AISettingsResponse,
    status_code=status.HTTP_200_OK,
)
async def get_ai_models(
    current_user: UserResponse = Depends(get_current_user),
) -> AISettingsResponse:
    """
    Lấy danh sách các mô hình khả dụng, phân tách thành nhánh Chat và nhánh Embedding.
    Yêu cầu token xác thực Admin.
    """
    # Import cục bộ để tránh circular import
    from app.shared.ai import get_ai_service
    ai_service = get_ai_service()

    raw_models = await ai_service.list_models()
    active_model = get_active_model()
    active_embedding_model = get_active_embedding_model()

    chat_models = []
    embedding_models = []

    for model in raw_models:
        model_id = model.get("id", "").lower()
        # Phân loại dựa trên tên model chứa từ khóa 'embed' hoặc 'embedding'
        if "embed" in model_id or "embedding" in model_id:
            embedding_models.append(model)
        else:
            chat_models.append(model)

    return AISettingsResponse(
        active_model=active_model,
        active_embedding_model=active_embedding_model,
        chat_models=chat_models,
        embedding_models=embedding_models,
        embedding_priority_list=get_embedding_priority_list()
    )


@ai_hub_router.post(
    "/settings",
    status_code=status.HTTP_200_OK,
)
async def update_ai_settings(
    payload: AISettingsUpdateRequest,
    current_user: UserResponse = Depends(get_current_user),
) -> dict[str, str]:
    """
    Cập nhật model active (chat hoặc embedding) được chọn để sử dụng cho toàn bộ hệ thống.
    Yêu cầu token xác thực Admin.
    """
    updated = []
    if payload.active_model is not None:
        save_active_model(payload.active_model)
        updated.append(f"active_model={payload.active_model}")
    if payload.active_embedding_model is not None:
        save_active_embedding_model(payload.active_embedding_model)
        updated.append(f"active_embedding_model={payload.active_embedding_model}")

    return {"message": f"Successfully updated settings: {', '.join(updated)}"}


@ai_hub_router.get(
    "/logs",
    response_model=AILogListResponse,
    status_code=status.HTTP_200_OK,
)
async def get_ai_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    model: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    user_id: Optional[uuid.UUID] = Query(None),
    model_type: Optional[str] = Query(None, enum=["chat", "embedding"]),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> AILogListResponse:
    """
    Lấy danh sách nhật ký cuộc gọi AI có phân trang và bộ lọc.
    Yêu cầu token xác thực Admin.
    """
    total, items = await ai_hub_service.get_logs(
        db,
        page=page,
        page_size=page_size,
        model=model,
        status_filter=status_filter,
        user_id=user_id,
        model_type=model_type
    )
    return AILogListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items
    )


@ai_hub_router.get(
    "/spend",
    response_model=AISpendResponse,
    status_code=status.HTTP_200_OK,
)
async def get_ai_spend(
    period: str = Query("day", enum=["day", "month", "year", "all"]),
    model_type: Optional[str] = Query(None, enum=["chat", "embedding"]),
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> AISpendResponse:
    """
    Lấy dữ liệu thống kê chi tiêu (Spend Analytics) theo thời gian (ngày, tháng, năm, toàn bộ)
    và chi tiết phân bổ theo người dùng.
    Yêu cầu token xác thực Admin.
    """
    time_series, user_spend = await ai_hub_service.get_spend_statistics(db, period=period, model_type=model_type)
    return AISpendResponse(time_series=time_series, user_spend=user_spend)


@ai_hub_router.post(
    "/playground",
    response_model=AIPlaygroundResponse,
    status_code=status.HTTP_200_OK,
)
async def call_ai_playground(
    payload: AIPlaygroundRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> AIPlaygroundResponse:
    """
    Thực hiện cuộc gọi thử nghiệm trực tiếp từ Playground (ghi nhận logs theo tên Admin đang đăng nhập).
    Yêu cầu token xác thực Admin.
    """
    # Import cục bộ để tránh circular import
    from app.shared.ai import get_ai_service
    ai_service = get_ai_service()

    start_time = time.time()
    try:
        response_meta = {}
        response = await ai_service.generate_text(
            prompt=payload.prompt,
            model=payload.model,
            system_instruction=payload.system_prompt,
            temperature=payload.temperature,
            max_tokens=payload.max_tokens,
            user_id=current_user.id,
            username=current_user.username,
            db=db,
            response_meta=response_meta
        )
        latency_ms = int((time.time() - start_time) * 1000)
        actual_model = response_meta.get("actual_model", payload.model)
        return AIPlaygroundResponse(
            response=response,
            latency_ms=latency_ms,
            actual_model=actual_model
        )
    except httpx.HTTPStatusError as e:
        # Lỗi phản hồi từ OmniRoute Gateway (hết token, API key lỗi, v.v.)
        try:
            err_data = e.response.json()
            err_msg = err_data.get("error", {}).get("message") or e.response.text
        except Exception:
            err_msg = e.response.text
        
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OmniRoute Gateway Error: {err_msg}"
        )
    except httpx.RequestError as e:
        # Lỗi kết nối mạng tới OmniRoute Gateway (timeout, connection refused)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Không thể kết nối đến OmniRoute Gateway: {str(e)}"
        )
    except Exception as e:
        # Các lỗi hệ thống khác
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi hệ thống khi gọi mô hình AI: {str(e)}"
        )


@ai_hub_router.post(
    "/embedding-playground",
    response_model=AIEmbeddingPlaygroundResponse,
    status_code=status.HTTP_200_OK,
)
async def call_ai_embedding_playground(
    payload: AIEmbeddingPlaygroundRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
) -> AIEmbeddingPlaygroundResponse:
    """
    Thực hiện vector hóa thử nghiệm từ Embedding Settings (ghi nhận logs theo tên Admin).
    Yêu cầu token xác thực Admin.
    """
    from app.shared.ai import get_ai_service
    ai_service = get_ai_service()

    start_time = time.time()
    try:
        response_meta = {}
        embedding = await ai_service.generate_embedding(
            text=payload.input,
            model=payload.model,
            user_id=current_user.id,
            username=current_user.username,
            db=db,
            response_meta=response_meta
        )
        latency_ms = int((time.time() - start_time) * 1000)
        actual_model = response_meta.get("actual_model", payload.model)
        
        return AIEmbeddingPlaygroundResponse(
            embedding=embedding,
            dimensions=len(embedding),
            latency_ms=latency_ms,
            actual_model=actual_model
        )
    except httpx.HTTPStatusError as e:
        try:
            err_data = e.response.json()
            err_msg = err_data.get("error", {}).get("message") or e.response.text
        except Exception:
            err_msg = e.response.text
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OmniRoute Gateway Error: {err_msg}"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Không thể kết nối đến OmniRoute Gateway: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi hệ thống khi gọi mô hình Embedding: {str(e)}"
        )

