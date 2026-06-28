import json
import uuid
import httpx
from datetime import datetime, UTC
from typing import Optional
from decimal import Decimal

from loguru import logger
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException
from app.modules.ai.models import AISetting, AIModelPricing, AIUsageLog
from app.modules.ai.providers import AIFactory, clean_json_response
from app.modules.ai.gemini_service import GeminiModelDiscoveryService
from app.modules.ai.schemas import (
    AIGenerateSEORequest,
    AIGenerateSEOResponse,
    AISettingUpdate,
    AIModelPricingCreate,
    AITestConnectionRequest,
    AITestConnectionResponse,
    AIDetectedModelResponse,
    AISpendingByModelResponse,
)
from app.shared.security.encryption import decrypt_data, encrypt_data


class AIService:
    """Nghiệp vụ quản lý AI Settings, tính toán Token và giới hạn ngân sách hàng tháng."""

    async def get_active_setting(self, db: AsyncSession, setting_type: str = "text") -> AISetting:
        """Lấy cấu hình AI đang hoạt động theo loại. Tạo mặc định nếu trống."""
        # Tự động đảm bảo cột setting_type tồn tại trong DB (PostgreSQL / SQLite)
        try:
            from sqlalchemy import text
            async with db.begin_nested():
                await db.execute(text("SELECT setting_type FROM ai_settings LIMIT 1;"))
        except Exception:
            try:
                from sqlalchemy import text
                await db.execute(text("ALTER TABLE ai_settings ADD COLUMN setting_type VARCHAR(20) DEFAULT 'text';"))
                await db.commit()
                logger.info("Successfully added setting_type column to ai_settings table.")
            except Exception as ex:
                logger.warning(f"Failed to auto-add column setting_type: {str(ex)}")

        query = select(AISetting).where(
            AISetting.is_active == True,
            AISetting.setting_type == setting_type
        )
        result = await db.execute(query)
        setting = result.scalar_one_or_none()
        
        if not setting:
            if setting_type == "text":
                setting = AISetting(
                    provider="gemini",
                    setting_type="text",
                    model="gemini-2.5-flash",
                    temperature=0.2,
                    max_tokens=1000,
                    timeout=30,
                    is_enabled=True,
                    is_active=True,
                    monthly_budget_limit=50.0000,
                    monthly_spent=0.0000,
                    budget_reset_day=1,
                    currency="USD"
                )
            else:  # embedding
                setting = AISetting(
                    provider="gemini",
                    setting_type="embedding",
                    model="text-embedding-004",
                    temperature=0.0,
                    max_tokens=1,
                    timeout=30,
                    is_enabled=True,
                    is_active=True,
                    monthly_budget_limit=10.0000,
                    monthly_spent=0.0000,
                    budget_reset_day=1,
                    currency="USD"
                )
            db.add(setting)
            await db.flush()
            
        return setting

    async def update_setting(
        self, db: AsyncSession, data: AISettingUpdate, current_user_id: uuid.UUID
    ) -> AISetting:
        """Cập nhật cấu hình AI. Mã hóa API Key nếu thay đổi."""
        setting = await self.get_active_setting(db, data.setting_type)
        update_data = data.model_dump(exclude_unset=True)
        # Loại bỏ setting_type khỏi các trường update trực tiếp
        update_data.pop("setting_type", None)

        if "api_key" in update_data:
            api_key_raw = update_data.pop("api_key")
            if api_key_raw:
                setting.api_key_encrypted = encrypt_data(api_key_raw)
            else:
                setting.api_key_encrypted = None

        for field, value in update_data.items():
            setattr(setting, field, value)
            
        setting.updated_by = current_user_id
        setting.updated_at = datetime.now(UTC)

        db.add(setting)
        await db.flush()
        
        logger.info(f"AI settings ({data.setting_type}) updated by user {current_user_id}")
        return setting

    # ──────────────────────────────────────────
    # Model Pricing Management
    # ──────────────────────────────────────────

    async def get_pricings(self, db: AsyncSession, setting_type: Optional[str] = None) -> list[AIModelPricing]:
        """Lấy danh sách bảng giá các model hiện có, lọc theo loại nếu cần."""
        query = select(AIModelPricing).order_by(AIModelPricing.provider, AIModelPricing.model_name)
        result = await db.execute(query)
        pricings = list(result.scalars().all())
        
        if setting_type:
            filtered = []
            for p in pricings:
                m_name_lower = p.model_name.lower()
                is_embed = "embed" in m_name_lower
                if setting_type == "embedding" and is_embed:
                    filtered.append(p)
                elif setting_type == "text" and not is_embed:
                    filtered.append(p)
            return filtered
            
        return pricings

    async def update_model_pricing(
        self, db: AsyncSession, data: AIModelPricingCreate
    ) -> AIModelPricing:
        """Thêm hoặc cập nhật đơn giá token của một model."""
        query = select(AIModelPricing).where(
            AIModelPricing.provider == data.provider,
            AIModelPricing.model_name == data.model_name
        )
        result = await db.execute(query)
        pricing = result.scalar_one_or_none()

        if not pricing:
            pricing = AIModelPricing(
                provider=data.provider,
                model_name=data.model_name,
                input_price_per_1m=data.input_price_per_1m,
                output_price_per_1m=data.output_price_per_1m
            )
        else:
            pricing.input_price_per_1m = data.input_price_per_1m
            pricing.output_price_per_1m = data.output_price_per_1m
            
        db.add(pricing)
        await db.flush()
        logger.info(f"Model pricing updated: {data.provider}/{data.model_name}")
        return pricing

    # ──────────────────────────────────────────
    # Usage Logs
    # ──────────────────────────────────────────

    async def get_usage_logs(
        self, db: AsyncSession, limit: int = 100, offset: int = 0
    ) -> list[AIUsageLog]:
        """Lấy danh sách nhật ký sử dụng AI phục vụ thống kê báo cáo."""
        query = select(AIUsageLog).order_by(desc(AIUsageLog.created_at)).offset(offset).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    # ──────────────────────────────────────────
    # Budget Guard & Generation
    # ──────────────────────────────────────────

    def _check_and_reset_budget(self, setting: AISetting, db: AsyncSession) -> None:
        """Kiểm tra và tự động reset hạn mức tháng nếu bước sang tháng mới."""
        now = datetime.now(UTC)
        if setting.updated_at:
            last_update = setting.updated_at
            if now.year != last_update.year or now.month != last_update.month:
                if now.day >= setting.budget_reset_day:
                    setting.monthly_spent = Decimal("0.0000")
                    setting.updated_at = now
                    db.add(setting)
                    logger.info("Monthly AI budget spending reset successfully.")

    async def generate_seo(
        self, db: AsyncSession, payload: AIGenerateSEORequest, current_user_id: uuid.UUID
    ) -> AIGenerateSEOResponse:
        """
        Gọi trợ lý AI để sinh SEO, tự động đếm token, quy đổi chi phí và cập nhật ngân sách.
        """
        # 1. Lấy cấu hình AI
        setting = await self.get_active_setting(db)
        
        if not setting.is_enabled:
            raise BadRequestException(
                message="Trợ lý AI hiện đang bị tắt trong hệ thống cấu hình",
                error_code="AI_ASSISTANT_DISABLED"
            )

        if not setting.api_key_encrypted:
            raise BadRequestException(
                message="Chưa cấu hình API Key cho nhà cung cấp AI trong hệ thống",
                error_code="AI_API_KEY_MISSING"
            )

        # 2. Reset ngân sách hàng tháng nếu đến kỳ
        self._check_and_reset_budget(setting, db)

        # 3. Kiểm tra hạn mức chi tiêu còn lại
        if setting.monthly_spent >= setting.monthly_budget_limit:
            raise BadRequestException(
                message="Hạn mức chi tiêu AI hàng tháng của website trường đã hết. Vui lòng liên hệ Admin.",
                error_code="AI_BUDGET_EXCEEDED"
            )

        # 4. Giải mã API Key
        api_key = decrypt_data(setting.api_key_encrypted)
        if not api_key:
            raise BadRequestException(
                message="Không thể giải mã API Key. Vui lòng cấu hình lại API Key trong AI Settings.",
                error_code="AI_DECRYPTION_ERROR"
            )

        # 5. Chuẩn bị prompt
        system_instruction = (
            "Bạn là một trợ lý chuyên gia tối ưu hóa SEO (SEO Specialist) cho website Trường Kỹ thuật và Công nghệ - Đại học Vinh.\n"
            "Nhiệm vụ của bạn là phân tích tiêu đề, mô tả tóm tắt, nội dung và chuyên mục được cung cấp để sinh dữ liệu SEO tối ưu bằng tiếng Việt dưới định dạng JSON chứa các trường sau:\n"
            "{\n"
            '  "seo_title": "Tiêu đề SEO tối ưu dài từ 50 đến tối đa 60 ký tự, lôi cuốn, chứa từ khóa chính, BẮT BUỘC kết thúc bằng hậu tố: | Trường Kỹ thuật và Công nghệ - Đại học Vinh (nếu tiêu đề chính quá dài có thể viết ngắn gọn lại rồi ghép hậu tố để không vượt quá 60 ký tự)",\n'
            '  "seo_description": "Mô tả SEO tóm tắt lôi cuốn nội dung dài tối thiểu 120 ký tự và tối đa 160 ký tự để tăng tỷ lệ click (CTR), không chứa thẻ HTML, không bọc trong dấu ngoặc kép bên ngoài giá trị JSON",\n'
            '  "seo_keywords": "Danh sách các từ khóa ngắn gọn, ngăn cách bằng dấu phẩy, tối đa 8 từ khóa phù hợp nhất với nội dung"\n'
            "}\n\n"
            "YÊU CẦU QUAN TRỌNG:\n"
            "- Bạn BẮT BUỘC chỉ được trả về chuỗi JSON thô, không bọc markdown (không có ```json), không thêm bất kỳ văn bản giải thích nào khác.\n"
            "- Phải tuyệt đối tuân thủ định dạng JSON ví dụ trên."
        )

        prompt = (
            f"Hãy sinh thông tin SEO cho nội dung sau:\n"
            f"- Tiêu đề: {payload.title}\n"
            f"- Mô tả tóm tắt: {payload.description or 'Chưa có'}\n"
            f"- Chuyên mục liên quan: {payload.category_name or 'Chưa có'}\n"
            f"- Nội dung chi tiết: {payload.content or 'Chưa có'}\n"
        )

        # 6. Gọi Provider
        provider = AIFactory.get_provider(setting.provider)
        
        try:
            raw_response, prompt_tokens, completion_tokens = await provider.generate_response(
                prompt=prompt,
                system_instruction=system_instruction,
                model=setting.model,
                api_key=api_key,
                base_url=setting.base_url,
                temperature=setting.temperature,
                max_tokens=setting.max_tokens,
                timeout=setting.timeout
            )
            
            # 7. Tính toán chi phí thực tế dựa trên bảng giá
            pricing_query = select(AIModelPricing).where(
                AIModelPricing.provider == setting.provider,
                AIModelPricing.model_name == setting.model
            )
            pricing_result = await db.execute(pricing_query)
            pricing = pricing_result.scalar_one_or_none()
            
            if pricing:
                input_cost = Decimal(str(prompt_tokens)) * Decimal(str(pricing.input_price_per_1m)) / Decimal("1000000")
                output_cost = Decimal(str(completion_tokens)) * Decimal(str(pricing.output_price_per_1m)) / Decimal("1000000")
                cost = input_cost + output_cost
            else:
                # Nếu chưa cấu hình giá, lấy giá mặc định an toàn của Gemini Flash (0.075 USD / 1M input, 0.30 USD / 1M output)
                input_cost = Decimal(str(prompt_tokens)) * Decimal("0.075") / Decimal("1000000")
                output_cost = Decimal(str(completion_tokens)) * Decimal("0.30") / Decimal("1000000")
                cost = input_cost + output_cost

            # 8. Cập nhật số tiền đã chi tiêu và ghi log sử dụng
            setting.monthly_spent = Decimal(str(setting.monthly_spent)) + cost
            setting.updated_at = datetime.now(UTC)
            db.add(setting)

            log_entry = AIUsageLog(
                user_id=current_user_id,
                provider=setting.provider,
                model=setting.model,
                feature="generate_seo",
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                cost=cost
            )
            db.add(log_entry)
            await db.flush()

            # 9. Parse JSON kết quả gợi ý trả về
            clean_json = clean_json_response(raw_response)
            seo_dict = json.loads(clean_json)
            
            return AIGenerateSEOResponse(
                seo_title=seo_dict.get("seo_title", payload.title)[:255],
                seo_description=seo_dict.get("seo_description", payload.description or "")[:500],
                seo_keywords=seo_dict.get("seo_keywords", "")[:255]
            )
            
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON response from LLM: {raw_response}")
            raise BadRequestException(
                message="Dịch vụ AI phản hồi dữ liệu sai cấu trúc JSON yêu cầu. Vui lòng thử lại.",
                error_code="AI_PARSING_ERROR"
            )
        except Exception as e:
            if isinstance(e, BadRequestException):
                raise e
            logger.exception(f"Error occurred during AI Generation: {str(e)}")
            raise BadRequestException(
                message=f"Trợ lý AI gặp lỗi khi xử lý: {str(e)}",
                error_code="AI_GENERATION_FAILED"
            )

    async def fetch_openrouter_pricings(self) -> dict[str, tuple[Decimal, Decimal]]:
        """
        Gọi API public của OpenRouter để lấy đơn giá mới nhất của toàn bộ models.
        Trả về dict dạng: {"model_name": (input_price_per_1m, output_price_per_1m)}
        """
        url = "https://openrouter.ai/api/v1/models"
        pricings = {}
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get("data", []):
                        m_id = item.get("id", "")
                        price_info = item.get("pricing", {})
                        
                        try:
                            prompt_price = Decimal(str(price_info.get("prompt", 0))) * Decimal("1000000")
                            completion_price = Decimal(str(price_info.get("completion", 0))) * Decimal("1000000")
                            
                            pricings[m_id.lower()] = (prompt_price, completion_price)
                            
                            if "/" in m_id:
                                short_id = m_id.split("/")[-1]
                                pricings[short_id.lower()] = (prompt_price, completion_price)
                        except Exception:
                            continue
        except Exception as e:
            logger.warning(f"Failed to fetch real-time AI pricings from OpenRouter: {str(e)}")
            
        return pricings

    async def test_connection(self, db: AsyncSession, payload: AITestConnectionRequest) -> AITestConnectionResponse:
        """Kiểm tra kết nối, tự động phát hiện danh sách model và tự động cập nhật bảng giá."""
        api_key = payload.api_key
        
        # 1. Hạn chế provider duy nhất là gemini
        provider_name = payload.provider.lower()
        if provider_name != "gemini":
            raise BadRequestException(
                message=f"Hệ thống chỉ hỗ trợ Google Gemini. Provider '{payload.provider}' không được phép.",
                error_code="UNSUPPORTED_AI_PROVIDER"
            )

        # 2. Lấy cấu hình theo setting_type và kiểm tra hạn mức
        setting = await self.get_active_setting(db, payload.setting_type)
        self._check_and_reset_budget(setting, db)

        if setting.monthly_spent >= setting.monthly_budget_limit:
            raise BadRequestException(
                message="Hạn mức chi tiêu AI hàng tháng của hệ thống đã vượt giới hạn cho phép.",
                error_code="AI_BUDGET_EXCEEDED"
            )

        # Nếu bỏ trống api_key -> Đọc key hiện tại đang lưu
        if not api_key:
            if not setting.api_key_encrypted:
                return AITestConnectionResponse(
                    success=False,
                    message="Kiểm thử thất bại. Không tìm thấy API Key nào trong hệ thống."
                )
            api_key = decrypt_data(setting.api_key_encrypted)

        detected_model_names = []
        active_model = None
        usage_records = []

        # 3. Gọi GeminiModelDiscoveryService để lấy danh sách và test tìm model hoạt động tốt nhất
        discovery_service = GeminiModelDiscoveryService()
        try:
            active_model, detected_model_names, usage_records = await discovery_service.discover_and_select_active_model(
                api_key=api_key,
                setting_type=payload.setting_type,
                base_url=payload.base_url,
                timeout=payload.timeout
            )
        except Exception as e:
            logger.warning(f"Gemini auto-discovery failed during connection test: {str(e)}")
            return AITestConnectionResponse(
                success=False,
                message="Kiểm thử kết nối tới AI Provider thất bại. API Key không hoạt động hoặc không đúng.",
                error_details=str(e)
            )

        # 4. Lưu model hoạt động được vào AISetting nếu connection test ok.
        # Ưu tiên giữ nguyên model người dùng chọn test (payload.model) nếu nó khả dụng.
        if payload.model and payload.model in detected_model_names:
            setting.model = payload.model
        elif active_model:
            setting.model = active_model
        db.add(setting)

        # 5. Đồng bộ hóa giá từ OpenRouter
        openrouter_prices = await self.fetch_openrouter_pricings()
        detected_models_response = []
        
        # 6. Ghi nhận/Cập nhật bảng giá cho các model phát hiện được
        for m_name in detected_model_names:
            m_key = m_name.lower()
            
            input_price = None
            output_price = None
            
            if m_key in openrouter_prices:
                input_price, output_price = openrouter_prices[m_key]
            else:
                # Chỉ lấy giá mặc định cho các model hệ thống chính yếu
                if "gemini-2.5-flash" in m_key or "gemini-2.0-flash" in m_key or "gemini-1.5-flash" in m_key:
                    input_price, output_price = Decimal("0.0750"), Decimal("0.3000")
                elif "gemini-2.5-pro" in m_key or "gemini-2.0-pro" in m_key or "gemini-1.5-pro" in m_key:
                    input_price, output_price = Decimal("1.2500"), Decimal("5.0000")
                elif "embedding" in m_key:
                    input_price, output_price = Decimal("0.0400"), Decimal("0.0000")
                elif "gemini" in m_key:
                    input_price, output_price = Decimal("0.0750"), Decimal("0.3000")

            # Nếu không xác định được giá, bỏ qua model này
            if input_price is None or output_price is None:
                logger.info(f"Model {m_name} does not have pricing info, skipping.")
                continue

            detected_models_response.append(
                AIDetectedModelResponse(
                    model_name=m_name,
                    input_price_per_1m=float(input_price),
                    output_price_per_1m=float(output_price)
                )
            )

            # Tự động lưu/cập nhật vào bảng ai_model_pricing
            pricing_query = select(AIModelPricing).where(AIModelPricing.model_name == m_name)
            pricing_res = await db.execute(pricing_query)
            pricing = pricing_res.scalar_one_or_none()
            
            if pricing:
                pricing.provider = payload.provider
                pricing.input_price_per_1m = input_price
                pricing.output_price_per_1m = output_price
                pricing.updated_at = datetime.now(UTC)
            else:
                pricing = AIModelPricing(
                    id=uuid.uuid4(),
                    provider=payload.provider,
                    model_name=m_name,
                    input_price_per_1m=input_price,
                    output_price_per_1m=output_price,
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC)
                )
            db.add(pricing)

        # 7. Tính toán chi phí thực sự tiêu tốn trong Test Connection và lưu logs
        detected_model_set = {m.model_name for m in detected_models_response}
        total_test_cost = Decimal("0.000000")
        
        for rec in usage_records:
            model_used = rec["model"]
            p_tokens = rec["prompt_tokens"]
            c_tokens = rec["completion_tokens"]
            
            if p_tokens > 0 or c_tokens > 0:
                input_p = Decimal("0.0750")
                output_p = Decimal("0.3000")
                m_key = model_used.lower()
                
                # Check trong OpenRouter prices
                if m_key in openrouter_prices:
                    input_p, output_p = openrouter_prices[m_key]
                else:
                    if "gemini-2.5-pro" in m_key or "gemini-2.0-pro" in m_key or "gemini-1.5-pro" in m_key:
                        input_p, output_p = Decimal("1.2500"), Decimal("5.0000")
                    elif "embedding" in m_key:
                        input_p, output_p = Decimal("0.0400"), Decimal("0.0000")
                
                cost = (Decimal(str(p_tokens)) * input_p + Decimal(str(c_tokens)) * output_p) / Decimal("1000000")
                total_test_cost += cost
                
                log = AIUsageLog(
                    id=uuid.uuid4(),
                    user_id=None,
                    provider="gemini",
                    model=model_used,
                    feature="connection_test",
                    prompt_tokens=p_tokens,
                    completion_tokens=c_tokens,
                    total_tokens=p_tokens + c_tokens,
                    cost=cost,
                    created_at=datetime.now(UTC)
                )
                db.add(log)
                
        if total_test_cost > 0:
            setting.monthly_spent = Decimal(str(setting.monthly_spent)) + total_test_cost
            setting.updated_at = datetime.now(UTC)
            db.add(setting)

        # 8. Dọn dẹp các model không còn khả dụng và chưa từng được sử dụng
        # CHỈ dọn dẹp model cùng loại (text hoặc embedding) để tránh xóa chéo
        db_pricings_query = select(AIModelPricing).where(AIModelPricing.provider == payload.provider)
        db_pricings_res = await db.execute(db_pricings_query)
        db_pricings = db_pricings_res.scalars().all()
        
        for db_pricing in db_pricings:
            m_name_lower = db_pricing.model_name.lower()
            is_embed_model = "embed" in m_name_lower
            
            # Chỉ xử lý model cùng loại với setting_type đang test
            if payload.setting_type == "embedding" and not is_embed_model:
                continue  # Không động vào model text khi đang test embedding
            if payload.setting_type == "text" and is_embed_model:
                continue  # Không động vào model embedding khi đang test text
            
            if db_pricing.model_name not in detected_model_set:
                # Kiểm tra xem model này đã từng có usage log chưa
                usage_query = select(AIUsageLog).where(
                    AIUsageLog.provider == payload.provider,
                    AIUsageLog.model == db_pricing.model_name
                ).limit(1)
                usage_res = await db.execute(usage_query)
                has_used = usage_res.scalar_one_or_none() is not None
                
                if not has_used:
                    logger.info(f"Removing obsolete unused model pricing: {payload.provider}/{db_pricing.model_name}")
                    await db.delete(db_pricing)

        await db.flush()

        model_selected_msg = f" Đã tự động chọn và lưu model hoạt động tốt nhất '{active_model}' làm mặc định cho loại '{payload.setting_type}'." if active_model else ""
        return AITestConnectionResponse(
            success=True,
            message=f"Kết nối thành công! Đã phát hiện và tự động đồng bộ {len(detected_models_response)} models khả dụng.{model_selected_msg}",
            detected_models=detected_models_response
        )

    async def get_spending_by_model(self, db: AsyncSession, setting_type: str = "text") -> list[AISpendingByModelResponse]:
        """
        Tính tổng số tiền đã tiêu thụ theo từng Model AI trong chu kỳ ngân sách tháng này.
        """
        # 1. Lấy hạn mức và chu kỳ reset
        setting = await self.get_active_setting(db, setting_type)
        limit = float(setting.monthly_budget_limit) if setting.monthly_budget_limit else 1.0
        reset_day = setting.budget_reset_day or 1

        # 2. Tính toán ngày bắt đầu chu kỳ ngân sách hiện tại
        now = datetime.now(UTC)
        try:
            start_date = datetime(now.year, now.month, reset_day, tzinfo=UTC)
            if now.day < reset_day:
                # Nếu chưa tới ngày reset tháng này, kỳ ngân sách bắt đầu từ tháng trước
                if now.month == 1:
                    start_date = datetime(now.year - 1, 12, reset_day, tzinfo=UTC)
                else:
                    start_date = datetime(now.year, now.month - 1, reset_day, tzinfo=UTC)
        except ValueError:
            # Đề phòng lỗi ValueError nếu tháng đó không có reset_day (ví dụ ngày 31 mà tháng 2)
            start_date = datetime(now.year, now.month, 1, tzinfo=UTC)

        # 3. Query tính tổng tiền tiêu thụ group by model và provider
        query = (
            select(
                AIUsageLog.provider,
                AIUsageLog.model,
                func.sum(AIUsageLog.cost).label("total_cost")
            )
            .where(AIUsageLog.created_at >= start_date)
            .group_by(AIUsageLog.provider, AIUsageLog.model)
        )
        
        result = await db.execute(query)
        rows = result.all()
        
        spending_list = []
        for row in rows:
            provider = row.provider
            model = row.model
            
            # Lọc model: nếu setting_type là embedding thì chỉ lấy model có chữ "embed"
            # nếu setting_type là text thì lấy model không chứa chữ "embed"
            is_embed_model = "embed" in model.lower()
            if (setting_type == "embedding" and not is_embed_model) or (setting_type == "text" and is_embed_model):
                continue
                
            total_spent = float(row.total_cost) if row.total_cost is not None else 0.0
            
            # Tính phần trăm so với hạn mức ngân sách tháng
            percentage = (total_spent / limit) * 100.0 if limit > 0 else 0.0
            
            spending_list.append(
                AISpendingByModelResponse(
                    provider=provider,
                    model=model,
                    total_spent=round(total_spent, 6),
                    percentage_of_limit=round(percentage, 2)
                )
            )
            
        return spending_list

    async def sync_active_provider_models(self, db: AsyncSession) -> None:
        """
        Tự động quét và đồng bộ lại models của provider đang hoạt động.
        Sử dụng cho scheduler tự động chạy lúc 00:00 hàng ngày.
        """
        for setting_type in ["text", "embedding"]:
            setting = await self.get_active_setting(db, setting_type)
            if not setting.is_enabled or not setting.api_key_encrypted:
                logger.info(f"AI Sync scheduler: AI {setting_type} is disabled or API Key is missing. Skipping sync.")
                continue

            api_key = decrypt_data(setting.api_key_encrypted)
            payload = AITestConnectionRequest(
                provider=setting.provider,
                setting_type=setting_type,
                base_url=setting.base_url,
                api_key=api_key,
                model=setting.model or ("gemini-2.5-flash" if setting_type == "text" else "text-embedding-004"),
                timeout=15
            )

            logger.info(f"AI Sync scheduler: Auto-syncing models for active provider '{setting.provider}' ({setting_type})...")
            # Gọi chính xác hàm test_connection để quét, ping thử, chọn model tốt nhất, cập nhật bảng giá và dọn dẹp model cũ
            await self.test_connection(db, payload)


ai_service = AIService()
