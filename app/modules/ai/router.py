from typing import Optional
from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.audit.service import log_action
from app.modules.auth.dependencies import has_permission
from app.modules.auth.schemas import UserResponse
from app.modules.ai.schemas import (
    AIGenerateSEORequest,
    AIGenerateSEOResponse,
    AISettingResponse,
    AISettingUpdate,
    AIModelPricingCreate,
    AIModelPricingResponse,
    AIUsageLogResponse,
    AITestConnectionRequest,
    AITestConnectionResponse,
    AISpendingByModelResponse,
)
from app.modules.ai.service import ai_service

ai_router = APIRouter()


# ──────────────────────────────────────────────
# Admin AI Settings CRUD
# ──────────────────────────────────────────────

@ai_router.get("/settings", response_model=AISettingResponse)
async def get_ai_settings(
    setting_type: str = Query(default="text", description="Loại cấu hình (text hoặc embedding)"),
    current_user: UserResponse = Depends(has_permission("ai.view")),
    db: AsyncSession = Depends(get_db),
) -> AISettingResponse:
    """
    Lấy thông tin cấu hình kết nối trợ lý AI hiện tại.
    API Key đã được che đi bảo mật.
    Quyền yêu cầu: ai.view
    """
    setting = await ai_service.get_active_setting(db, setting_type)
    return AISettingResponse.model_validate(setting)


@ai_router.put("/settings", response_model=AISettingResponse)
async def update_ai_settings(
    request: Request,
    payload: AISettingUpdate,
    current_user: UserResponse = Depends(has_permission("ai.update")),
    db: AsyncSession = Depends(get_db),
) -> AISettingResponse:
    """
    Cập nhật thông tin kết nối và lựa chọn Model AI.
    API Key truyền lên sẽ được mã hóa an toàn ở Backend.
    Quyền yêu cầu: ai.update
    """
    setting = await ai_service.update_setting(db, payload, current_user.id)
    await log_action(
        db, current_user, "AI_SETTINGS_UPDATED", "ai_setting", setting.id,
        payload.model_dump(exclude_unset=True, exclude={"api_key"}),
        request,
    )
    await db.commit()
    return AISettingResponse.model_validate(setting)


# ──────────────────────────────────────────────
# AI Model Pricing
# ──────────────────────────────────────────────

@ai_router.get("/pricing", response_model=list[AIModelPricingResponse])
async def list_model_pricings(
    setting_type: Optional[str] = Query(default=None, description="Lọc theo loại cấu hình (text hoặc embedding)"),
    current_user: UserResponse = Depends(has_permission("ai.view")),
    db: AsyncSession = Depends(get_db),
) -> list[AIModelPricingResponse]:
    """
    Lấy bảng đơn giá Input/Output token của các model AI.
    Quyền yêu cầu: ai.view
    """
    pricings = await ai_service.get_pricings(db, setting_type)
    return [AIModelPricingResponse.model_validate(p) for p in pricings]


@ai_router.post("/pricing", response_model=AIModelPricingResponse)
async def create_or_update_model_pricing(
    request: Request,
    payload: AIModelPricingCreate,
    current_user: UserResponse = Depends(has_permission("ai.update")),
    db: AsyncSession = Depends(get_db),
) -> AIModelPricingResponse:
    """
    Thêm mới hoặc cập nhật đơn giá của một dòng model AI.
    Quyền yêu cầu: ai.update
    """
    pricing = await ai_service.update_model_pricing(db, payload)
    await log_action(
        db, current_user, "AI_MODEL_PRICING_UPDATED", "ai_model_pricing", pricing.id,
        payload.model_dump(),
        request,
    )
    await db.commit()
    return AIModelPricingResponse.model_validate(pricing)


# ──────────────────────────────────────────────
# AI Usage Logs
# ──────────────────────────────────────────────

@ai_router.get("/usage-logs", response_model=list[AIUsageLogResponse])
async def list_ai_usage_logs(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    current_user: UserResponse = Depends(has_permission("ai.view")),
    db: AsyncSession = Depends(get_db),
) -> list[AIUsageLogResponse]:
    """
    Lấy danh sách nhật ký sử dụng AI phục vụ thống kê báo cáo và kiểm tra chi phí.
    Quyền yêu cầu: ai.view
    """
    logs = await ai_service.get_usage_logs(db, limit=limit, offset=offset)
    return [AIUsageLogResponse.model_validate(l) for l in logs]


# ──────────────────────────────────────────────
# AI Generation Actions
# ──────────────────────────────────────────────

@ai_router.post("/generate-seo", response_model=AIGenerateSEOResponse)
async def generate_seo_with_ai(
    payload: AIGenerateSEORequest,
    current_user: UserResponse = Depends(has_permission("ai.generate_seo")),
    db: AsyncSession = Depends(get_db),
) -> AIGenerateSEOResponse:
    """
    Gọi trợ lý AI để phân tích và đề xuất bộ thẻ Meta SEO (Title, Description, Keywords).
    Dữ liệu trả về chỉ hiển thị Preview, không tự ý ghi vào Database.
    Hệ thống tự động trừ hạn mức chi tiêu hàng tháng.
    Quyền yêu cầu: ai.generate_seo
    """
    result = await ai_service.generate_seo(db, payload, current_user.id)
    await db.commit()
    return result


@ai_router.post("/test-connection", response_model=AITestConnectionResponse)
async def test_ai_connection(
    payload: AITestConnectionRequest,
    current_user: UserResponse = Depends(has_permission("ai.test_connection")),
    db: AsyncSession = Depends(get_db),
) -> AITestConnectionResponse:
    """
    Kiểm tra kết nối trực tiếp đến nhà cung cấp AI với Key/Model được chọn.
    Giúp admin xác thực cấu hình trước khi lưu trữ chính thức.
    Quyền yêu cầu: ai.test_connection
    """
    result = await ai_service.test_connection(db, payload)
    await db.commit()
    return result


@ai_router.get("/spending-by-model", response_model=list[AISpendingByModelResponse])
async def get_spending_by_model(
    setting_type: str = Query(default="text", description="Loại cấu hình (text hoặc embedding)"),
    current_user: UserResponse = Depends(has_permission("ai.view")),
    db: AsyncSession = Depends(get_db),
) -> list[AISpendingByModelResponse]:
    """
    Lấy thống kê chi tiết chi tiêu của từng Model AI so với hạn mức trong tháng này.
    Quyền yêu cầu: ai.view
    """
    return await ai_service.get_spending_by_model(db, setting_type)
