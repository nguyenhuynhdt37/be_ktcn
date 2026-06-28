import json
import uuid
from decimal import Decimal
from datetime import datetime, timedelta, UTC
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.models import AISetting, AIModelPricing, AIUsageLog
from app.modules.ai.providers import clean_json_response
from app.shared.security.encryption import decrypt_data, encrypt_data


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _get_admin_token(client: AsyncClient) -> str:
    """Lấy token của admin (Super Admin seeded trong DB)."""
    resp = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "adminpassword"})
    assert resp.status_code == 200, f"Login thất bại: {resp.text}"
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ─── Tests ────────────────────────────────────────────────────────────────────

class TestAIEncryption:
    def test_encrypt_and_decrypt_api_key(self) -> None:
        """Kiểm tra mã hóa và giải mã API Key an toàn."""
        raw_key = "AIzaSyFakeKeyGemini123456"
        encrypted = encrypt_data(raw_key)
        
        assert encrypted != raw_key
        assert decrypt_data(encrypted) == raw_key

    def test_decrypt_empty_or_none_returns_empty(self) -> None:
        assert decrypt_data("") == ""
        assert decrypt_data(None) == ""


class TestAISettingsAPI:
    async def test_get_ai_settings_returns_default_settings(self, client: AsyncClient) -> None:
        """Kiểm tra xem API trả về cài đặt AI mặc định và che masked API Key."""
        token = await _get_admin_token(client)
        resp = await client.get("/api/v1/ai/settings", headers=_auth(token))
        
        assert resp.status_code == 200
        data = resp.json()
        assert "provider" in data
        assert "model" in data
        assert "monthly_budget_limit" in data
        assert "monthly_spent" in data
        # API Key không được lộ
        assert "api_key_encrypted" not in data
        assert "api_key" not in data

    async def test_update_ai_settings_encrypts_key(self, client: AsyncClient, db_session: AsyncSession) -> None:
        """Kiểm tra cập nhật cài đặt AI và API Key được mã hóa lưu trữ ở DB."""
        token = await _get_admin_token(client)
        new_key = "gemini-secret-key-test-encryption"
        
        payload = {
            "setting_type": "text",
            "provider": "gemini",
            "model": "gemini-2.5-flash",
            "api_key": new_key,
            "monthly_budget_limit": 100.0,
            "budget_reset_day": 5
        }
        
        resp = await client.put("/api/v1/ai/settings", json=payload, headers=_auth(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["provider"] == "gemini"
        assert data["model"] == "gemini-2.5-flash"
        assert data["api_key_masked"] == "••••••••••••••••"
        assert float(data["monthly_budget_limit"]) == 100.0

        # Lấy trực tiếp từ DB để kiểm chứng khóa đã được mã hóa chứ không lưu thô
        query = select(AISetting).where(AISetting.is_active == True, AISetting.setting_type == "text")
        result = await db_session.execute(query)
        db_setting = result.scalar_one()
        assert db_setting.api_key_encrypted != new_key
        assert decrypt_data(db_setting.api_key_encrypted) == new_key


class TestAIModelPricingAPI:
    async def test_list_pricing_returns_list(self, client: AsyncClient) -> None:
        token = await _get_admin_token(client)
        resp = await client.get("/api/v1/ai/pricing", headers=_auth(token))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_create_or_update_pricing(self, client: AsyncClient) -> None:
        token = await _get_admin_token(client)
        payload = {
            "provider": "openai",
            "model_name": "gpt-4o-mini-test-pricing",
            "input_price_per_1m": 0.1500,
            "output_price_per_1m": 0.6000
        }
        resp = await client.post("/api/v1/ai/pricing", json=payload, headers=_auth(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["model_name"] == "gpt-4o-mini-test-pricing"
        assert float(data["input_price_per_1m"]) == 0.1500


class TestAIGenerateSEOAndBudgetLimits:
    
    @patch("app.modules.ai.providers.GeminiProvider.generate_response", new_callable=AsyncMock)
    async def test_generate_seo_success_with_budget_and_logs(
        self, mock_gemini, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Kiểm tra gọi sinh SEO thành công, tự động trừ tiền và lưu log sử dụng."""
        token = await _get_admin_token(client)
        
        # Thiết lập đơn giá cho Gemini trong DB
        pricing_payload = {
            "provider": "gemini",
            "model_name": "gemini-2.5-flash",
            "input_price_per_1m": 0.0750,
            "output_price_per_1m": 0.3000
        }
        await client.post("/api/v1/ai/pricing", json=pricing_payload, headers=_auth(token))

        # Cấu hình AI Settings có sẵn key và bật
        settings_payload = {
            "setting_type": "text",
            "provider": "gemini",
            "model": "gemini-2.5-flash",
            "api_key": "AIzaSyFakeKeyValid",
            "is_enabled": True,
            "monthly_budget_limit": 50.0
        }
        await client.put("/api/v1/ai/settings", json=settings_payload, headers=_auth(token))

        # Mock LLM response: trả về JSON string + prompt_tokens + completion_tokens
        mock_response_json = json.dumps({
            "seo_title": "Tuyển sinh Đại học 2026 | Đại học ABC",
            "seo_description": "Thông báo tuyển sinh năm 2026 chính thức.",
            "seo_keywords": "tuyen sinh, dai hoc abc"
        })
        # Trả về tuple: (content, prompt_tokens, completion_tokens)
        mock_gemini.return_value = (mock_response_json, 1000000, 1000000)

        # Gọi API sinh SEO
        generate_payload = {
            "title": "Tuyển sinh năm 2026",
            "description": "Chương trình tuyển sinh đại học.",
            "content": "Nội dung chi tiết..."
        }
        
        resp = await client.post("/api/v1/ai/generate-seo", json=generate_payload, headers=_auth(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["seo_title"] == "Tuyển sinh Đại học 2026 | Đại học ABC"
        
        # Verify ngân sách bị trừ (cost = 1M * 0.075 / 1M + 1M * 0.30 / 1M = 0.075 + 0.3 = 0.375 USD)
        # Refresh session để đọc dữ liệu mới
        db_session.expire_all()
        query = select(AISetting).where(AISetting.is_active == True, AISetting.setting_type == "text")
        res = await db_session.execute(query)
        setting = res.scalar_one()
        assert float(setting.monthly_spent) > 0.0

        # Kiểm tra xem có lưu Usage Log không
        log_query = select(AIUsageLog).order_by(AIUsageLog.created_at.desc()).limit(1)
        log_res = await db_session.execute(log_query)
        usage_log = log_res.scalar_one_or_none()
        assert usage_log is not None
        assert usage_log.prompt_tokens == 1000000
        assert usage_log.completion_tokens == 1000000
        assert float(usage_log.cost) > 0.0

    async def test_generate_seo_blocked_when_budget_exceeded(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Kiểm tra chặn gọi API nếu đã tiêu dùng vượt hạn mức tháng."""
        token = await _get_admin_token(client)
        
        # Tạo cấu hình AI trước qua API
        settings_payload = {
            "setting_type": "text",
            "provider": "gemini",
            "model": "gemini-2.5-flash",
            "api_key": "AIzaSyFakeKeyValid",
            "is_enabled": True,
            "monthly_budget_limit": 50.0
        }
        await client.put("/api/v1/ai/settings", json=settings_payload, headers=_auth(token))

        # Set limit ngân sách cực kỳ nhỏ, và gán spent vượt limit
        setting_query = select(AISetting).where(AISetting.is_active == True, AISetting.setting_type == "text")
        result = await db_session.execute(setting_query)
        setting = result.scalar_one()
        setting.monthly_budget_limit = 10.0000
        setting.monthly_spent = 10.0005  # Đã vượt
        db_session.add(setting)
        await db_session.commit()

        # Gọi API sinh SEO
        generate_payload = {
            "title": "Tuyển sinh 2026",
            "description": "Mô tả nháp"
        }
        
        resp = await client.post("/api/v1/ai/generate-seo", json=generate_payload, headers=_auth(token))
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "AI_BUDGET_EXCEEDED"

    @patch("app.modules.ai.providers.GeminiProvider.generate_response", new_callable=AsyncMock)
    async def test_budget_reset_when_new_month_starts(
        self, mock_gemini, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Kiểm tra ngân sách tháng được tự động reset về 0 khi hệ thống chuyển sang tháng mới."""
        token = await _get_admin_token(client)
        
        # Thiết lập đơn giá cho Gemini trong DB
        pricing_payload = {
            "provider": "gemini",
            "model_name": "gemini-2.5-flash",
            "input_price_per_1m": 0.0750,
            "output_price_per_1m": 0.3000
        }
        await client.post("/api/v1/ai/pricing", json=pricing_payload, headers=_auth(token))

        # Tạo cấu hình AI trước qua API
        settings_payload = {
            "setting_type": "text",
            "provider": "gemini",
            "model": "gemini-2.5-flash",
            "api_key": "AIzaSyFakeKeyValid",
            "is_enabled": True,
            "monthly_budget_limit": 50.0
        }
        await client.put("/api/v1/ai/settings", json=settings_payload, headers=_auth(token))

        # Giả lập lần cập nhật gần nhất là tháng trước và đã tiêu vượt hạn mức
        last_month_date = datetime.now(UTC) - timedelta(days=32)
        
        setting_query = select(AISetting).where(AISetting.is_active == True, AISetting.setting_type == "text")
        result = await db_session.execute(setting_query)
        setting = result.scalar_one()
        setting.monthly_budget_limit = 10.0
        setting.monthly_spent = 15.0  # Vượt hạn mức tháng trước
        setting.updated_at = last_month_date  # Giả lập thời gian update là tháng trước
        db_session.add(setting)
        await db_session.commit()

        # Mock LLM response cho lượt gọi mới
        mock_response_json = json.dumps({
            "seo_title": "Tiêu đề mới",
            "seo_description": "Mô tả mới",
            "seo_keywords": "từ khóa"
        })
        mock_gemini.return_value = (mock_response_json, 1000000, 1000000)

        # Gọi API sinh SEO để trigger reset ngân sách
        generate_payload = {
            "title": "Tuyển sinh mới",
            "description": "Mô tả"
        }
        resp = await client.post("/api/v1/ai/generate-seo", json=generate_payload, headers=_auth(token))
        assert resp.status_code == 200
        
        # Đọc trực tiếp từ DB sau khi trigger reset -> monthly_spent phải bằng cost của lượt gọi mới (~0.0000225) thay vì 15.0
        db_session.expire_all()
        result = await db_session.execute(setting_query)
        setting = result.scalar_one()
        assert float(setting.monthly_spent) < 1.0  # Đã reset và chỉ tính tiền lần gọi mới
        assert float(setting.monthly_spent) > 0.0


class TestAITestConnectionAPI:

    @patch("app.modules.ai.gemini_service.GeminiModelDiscoveryService.discover_and_select_active_model", new_callable=AsyncMock)
    @patch("app.modules.ai.service.AIService.fetch_openrouter_pricings", new_callable=AsyncMock)
    async def test_connection_success(self, mock_prices, mock_discover, client: AsyncClient) -> None:
        """Kiểm tra gọi test connection phản hồi thành công, trả về models và đồng bộ đơn giá."""
        token = await _get_admin_token(client)
        mock_discover.return_value = (
            "gemini-2.5-flash", 
            ["gemini-2.5-flash", "gemini-2.5-pro"],
            [{"model": "gemini-2.5-flash", "prompt_tokens": 12, "completion_tokens": 5}]
        )
        
        # Giả lập bảng giá openrouter
        mock_prices.return_value = {
            "gemini-2.5-flash": (Decimal("0.0750"), Decimal("0.3000")),
            "gemini-2.5-pro": (Decimal("1.2500"), Decimal("5.0000"))
        }

        payload = {
            "provider": "gemini",
            "setting_type": "text",
            "model": "gemini-2.5-flash",
            "api_key": "AIzaSyFakeTestConnectionKey",
            "timeout": 5
        }
        
        resp = await client.post("/api/v1/ai/test-connection", json=payload, headers=_auth(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "thành công" in data["message"]
        assert len(data["detected_models"]) == 2
        assert data["detected_models"][0]["model_name"] == "gemini-2.5-flash"
        assert data["detected_models"][0]["input_price_per_1m"] == 0.0750

    @patch("app.modules.ai.gemini_service.GeminiModelDiscoveryService.discover_and_select_active_model", new_callable=AsyncMock)
    async def test_connection_failure(self, mock_discover, client: AsyncClient) -> None:
        """Kiểm tra bắt lỗi chính xác khi kết nối thất bại."""
        token = await _get_admin_token(client)
        # Giả lập lỗi API key không hợp lệ từ Google Gemini
        mock_discover.side_effect = Exception("API_KEY_INVALID: API key not valid")

        payload = {
            "provider": "gemini",
            "setting_type": "text",
            "model": "gemini-2.5-flash",
            "api_key": "InvalidKey",
            "timeout": 5
        }
        
        resp = await client.post("/api/v1/ai/test-connection", json=payload, headers=_auth(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False
        assert "API_KEY_INVALID" in data["error_details"]


class TestJSONCleaner:
    def test_clean_json_strips_markdown_tags(self) -> None:
        raw_llm_output = "```json\n{\n  \"seo_title\": \"Tuyển sinh\"\n}\n```"
        cleaned = clean_json_response(raw_llm_output)
        assert cleaned == "{\n  \"seo_title\": \"Tuyển sinh\"\n}"


class TestAISpendingByModelAPI:

    async def test_get_spending_by_model_success(self, client: AsyncClient, db_session: AsyncSession) -> None:
        """Kiểm tra API lấy thống kê chi tiêu theo model hoạt động chính xác."""
        token = await _get_admin_token(client)
        
        # 1. Thêm một số log sử dụng AI vào DB để giả lập chi tiêu
        log1 = AIUsageLog(
            id=uuid.uuid4(),
            user_id=None,
            provider="gemini",
            model="gemini-2.5-flash",
            feature="category_seo",
            prompt_tokens=1000,
            completion_tokens=2000,
            total_tokens=3000,
            cost=Decimal("0.1000"),
            created_at=datetime.now(UTC)
        )
        log2 = AIUsageLog(
            id=uuid.uuid4(),
            user_id=None,
            provider="gemini",
            model="gemini-2.5-flash",
            feature="category_seo",
            prompt_tokens=2000,
            completion_tokens=4000,
            total_tokens=6000,
            cost=Decimal("0.2000"),
            created_at=datetime.now(UTC)
        )
        log3 = AIUsageLog(
            id=uuid.uuid4(),
            user_id=None,
            provider="gemini",
            model="gemini-2.5-pro",
            feature="category_seo",
            prompt_tokens=1000,
            completion_tokens=2000,
            total_tokens=3000,
            cost=Decimal("0.5000"),
            created_at=datetime.now(UTC)
        )
        
        db_session.add_all([log1, log2, log3])
        await db_session.commit()
        
        # 2. Gọi API spending-by-model
        resp = await client.get("/api/v1/ai/spending-by-model", headers=_auth(token))
        assert resp.status_code == 200
        data = resp.json()
        
        # 3. Verify kết quả
        assert len(data) == 2
        
        # Sắp xếp để assert dễ dàng
        data_sorted = sorted(data, key=lambda x: x["model"])
        
        # gemini-2.5-flash: cost = 0.1000 + 0.2000 = 0.3000
        assert data_sorted[0]["model"] == "gemini-2.5-flash"
        assert data_sorted[0]["total_spent"] == 0.3000
        
        # gemini-2.5-pro: cost = 0.5000
        assert data_sorted[1]["model"] == "gemini-2.5-pro"
        assert data_sorted[1]["total_spent"] == 0.5000
        
        # Mặc định limit = 50.0. flashspent = 0.3 -> percentage = (0.3/50) * 100 = 0.6%
        assert data_sorted[0]["percentage_of_limit"] == 0.60
        assert data_sorted[1]["percentage_of_limit"] == 1.00


class TestAIDailySyncScheduler:

    @patch("app.modules.ai.gemini_service.GeminiModelDiscoveryService.discover_and_select_active_model", new_callable=AsyncMock)
    @patch("app.modules.ai.service.AIService.fetch_openrouter_pricings", new_callable=AsyncMock)
    async def test_sync_active_provider_models_success(self, mock_prices, mock_discover, db_session: AsyncSession) -> None:
        """Kiểm tra việc đồng bộ models hoạt động thành công của scheduler."""
        mock_discover.return_value = (
            "gemini-2.5-flash", 
            ["gemini-2.5-flash", "gemini-2.5-pro"],
            [{"model": "gemini-2.5-flash", "prompt_tokens": 12, "completion_tokens": 5}]
        )
        mock_prices.return_value = {
            "gemini-2.5-flash": (Decimal("0.0750"), Decimal("0.3000")),
            "gemini-2.5-pro": (Decimal("1.2500"), Decimal("5.0000"))
        }

        # Thiết lập settings trong DB
        from app.modules.ai.service import ai_service
        setting = await ai_service.get_active_setting(db_session)
        setting.is_enabled = True
        setting.provider = "gemini"
        setting.api_key_encrypted = encrypt_data("AIzaSyFakeActualTestKey")
        db_session.add(setting)
        await db_session.commit()

        # Gọi hàm sync tự động
        await ai_service.sync_active_provider_models(db_session)

        # Đọc lại settings và pricings để verify
        result_setting = await ai_service.get_active_setting(db_session)
        assert result_setting.model == "gemini-2.5-flash"

        # Check pricings DB
        pricing_query = select(AIModelPricing).where(AIModelPricing.provider == "gemini")
        pricing_res = await db_session.execute(pricing_query)
        pricings = pricing_res.scalars().all()
        assert len(pricings) == 2
        assert pricings[0].model_name == "gemini-2.5-flash"
        assert float(pricings[0].input_price_per_1m) == 0.0750

    async def test_sync_active_provider_models_disabled(self, db_session: AsyncSession) -> None:
        """Kiểm tra nếu AI bị tắt (is_enabled = False), scheduler sẽ bỏ qua không quét."""
        from app.modules.ai.service import ai_service
        setting = await ai_service.get_active_setting(db_session)
        setting.is_enabled = False
        setting.provider = "gemini"
        db_session.add(setting)
        await db_session.commit()

        with patch("app.modules.ai.gemini_service.GeminiModelDiscoveryService.discover_and_select_active_model") as mock_discover:
            await ai_service.sync_active_provider_models(db_session)
            mock_discover.assert_not_called()
