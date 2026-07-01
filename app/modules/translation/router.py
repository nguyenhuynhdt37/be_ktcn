from fastapi import APIRouter, Depends, status
from app.core.config import settings
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserResponse
from app.modules.translation.exceptions import BatchSizeExceededException
from app.modules.translation.schemas import TranslationRequest, BatchTranslationRequest
from app.modules.translation.service import translation_service

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
    Yêu cầu token xác thực Admin.
    """
    return await translation_service.translate_text(
        text=payload.text,
        target_languages=payload.target_languages
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
    Yêu cầu token xác thực Admin.
    """
    if len(payload.texts) > settings.TRANSLATION_MAX_BATCH_SIZE:
        raise BatchSizeExceededException(
            message=f"Số lượng đoạn văn bản cần dịch vượt quá giới hạn cho phép ({settings.TRANSLATION_MAX_BATCH_SIZE} chuỗi)"
        )
    return await translation_service.translate_batch(
        texts=payload.texts,
        target_languages=payload.target_languages
    )
