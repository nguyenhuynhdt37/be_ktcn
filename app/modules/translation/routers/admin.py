from fastapi import APIRouter, Depends, status
from app.core.config import settings
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserResponse
from app.modules.translation.exceptions import BatchSizeExceededException
from app.modules.translation.schemas import (
    TranslationRequest,
    BatchTranslationRequest,
    HTMLTranslationRequest,
    AISettingsUpdateRequest,
    AISettingsResponse,
)
from app.modules.translation.service import translation_service
from app.shared.ai import get_ai_service
from app.shared.ai.service import AIService, get_active_model, save_active_model

translation_router = APIRouter()


@translation_router.post(
    "",
    response_model=dict[str, str],
    status_code=status.HTTP_200_OK,
)
async def translate_text(
    payload: TranslationRequest,
    current_user: UserResponse = Depends(get_current_user),
) -> dict[str, str]:
    """
    Dịch tự động một văn bản tiếng Việt sang danh sách các ngôn ngữ đích chỉ định.
    Hỗ trợ truyền context để AI dịch chính xác theo ngữ cảnh.
    Yêu cầu token xác thực Admin.
    """
    return await translation_service.translate_text(
        text=payload.text,
        target_languages=payload.target_languages,
        context=payload.context
    )


@translation_router.post(
    "/batch",
    response_model=list[dict[str, str]],
    status_code=status.HTTP_200_OK,
)
async def translate_texts_batch(
    payload: BatchTranslationRequest,
    current_user: UserResponse = Depends(get_current_user),
) -> list[dict[str, str]]:
    """
    Dịch tự động hàng loạt đoạn văn bản tiếng Việt sang danh sách các ngôn ngữ đích chỉ định (Tối ưu hóa batching).
    Hỗ trợ truyền context để AI dịch chính xác theo ngữ cảnh cho toàn bộ danh sách.
    Yêu cầu token xác thực Admin.
    """
    if len(payload.texts) > settings.TRANSLATION_MAX_BATCH_SIZE:
        raise BatchSizeExceededException(
            message=f"Số lượng đoạn văn bản cần dịch vượt quá giới hạn cho phép ({settings.TRANSLATION_MAX_BATCH_SIZE} chuỗi)"
        )
    return await translation_service.translate_batch(
        texts=payload.texts,
        target_languages=payload.target_languages,
        context=payload.context
    )


@translation_router.post(
    "/html",
    response_model=dict[str, str],
    status_code=status.HTTP_200_OK,
)
async def translate_html(
    payload: HTMLTranslationRequest,
    current_user: UserResponse = Depends(get_current_user),
) -> dict[str, str]:
    """
    Dịch tự động nội dung HTML của trình soạn thảo văn bản (CKEditor) sang các ngôn ngữ chỉ định.
    Bảo toàn cấu trúc HTML, định dạng, CSS classes, liên kết, bảng biểu, hình ảnh.
    Hỗ trợ truyền context để AI dịch chính xác ngữ cảnh HTML.
    Yêu cầu token xác thực Admin.
    """
    return await translation_service.translate_html(
        html_content=payload.html,
        target_languages=payload.target_languages,
        context=payload.context
    )


@translation_router.get(
    "/ai/models",
    response_model=AISettingsResponse,
    status_code=status.HTTP_200_OK,
)
async def get_ai_models(
    current_user: UserResponse = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service),
) -> AISettingsResponse:
    """
    Lấy danh sách các model khả dụng từ Gateway và model active hiện tại.
    Yêu cầu token xác thực Admin.
    """
    models = await ai_service.list_models()
    active_model = get_active_model()
    return AISettingsResponse(
        active_model=active_model,
        models=models
    )


@translation_router.post(
    "/ai/settings",
    status_code=status.HTTP_200_OK,
)
async def update_ai_settings(
    payload: AISettingsUpdateRequest,
    current_user: UserResponse = Depends(get_current_user),
) -> dict[str, str]:
    """
    Cập nhật model active được chọn để sử dụng cho toàn bộ hệ thống.
    Yêu cầu token xác thực Admin.
    """
    save_active_model(payload.active_model)
    return {"message": f"Successfully updated active AI model to: {payload.active_model}"}
