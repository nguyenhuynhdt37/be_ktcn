from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.shared.ai.base import BaseAIProvider
from app.shared.ai.providers.omniroute import OmniRouteProvider
from app.shared.ai.config import get_active_model, save_active_model
from loguru import logger


class AIService:
    """
    AIService hoạt động như một lớp điều phối (Facade/Factory), giao tiếp với toàn bộ nghiệp vụ
    thông qua interface thống nhất mà không làm lộ chi tiết implementation của từng AI Provider.
    """

    def __init__(self) -> None:
        self._provider = self._init_provider()

    def _init_provider(self) -> BaseAIProvider:
        provider_name = settings.AI_PROVIDER.lower()
        api_key = settings.AI_API_KEY
        base_url = settings.AI_BASE_URL
        default_model = get_active_model()

        if provider_name == "omniroute":
            return OmniRouteProvider(
                api_key=api_key,
                base_url=base_url,
                default_model=default_model,
            )
        else:
            raise ValueError(f"Unsupported AI Provider: {provider_name}")

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        history: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """
        Giao tiếp với provider để sinh văn bản.
        Tự động lấy active model động nếu không chỉ định model cụ thể.
        """
        if "model" not in kwargs or kwargs["model"] is None:
            kwargs["model"] = get_active_model()

        return await self._provider.generate_text(
            prompt=prompt,
            system_instruction=system_instruction,
            history=history,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    async def generate_embedding(self, text: str, **kwargs: Any) -> List[float]:
        """
        Giao tiếp với provider để sinh vector embedding.
        """
        return await self._provider.generate_embedding(text=text, **kwargs)

    async def list_models(self) -> List[Dict[str, Any]]:
        """
        Lấy danh sách các model từ provider.
        """
        return await self._provider.list_models()
