from functools import lru_cache
from app.shared.ai.service import AIService


@lru_cache()
def get_ai_service() -> AIService:
    """
    FastAPI dependency hoặc Singleton instance provider cho AIService.
    """
    return AIService()


__all__ = ["AIService", "get_ai_service"]
