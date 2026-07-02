from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseAIProvider(ABC):
    """
    Lớp cơ sở trừu tượng (Abstract Base Class) cho tất cả AI Providers.
    Mọi provider tích hợp trong tương lai đều phải implement các phương thức này.
    """

    @abstractmethod
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
        Sinh văn bản (Text Generation) từ prompt được cung cấp.

        Args:
            prompt: Nội dung yêu cầu gửi tới AI.
            system_instruction: Chỉ thị hệ thống (system prompt) cho AI.
            history: Lịch sử trò chuyện dạng danh sách các dict.
            temperature: Độ sáng tạo của model (0.0 - 1.0).
            max_tokens: Số token tối đa trả về.
            **kwargs: Các tham số cấu hình bổ sung khác.

        Returns:
            str: Văn bản kết quả sinh ra bởi model.
        """
        pass

    @abstractmethod
    async def generate_embedding(self, text: str, **kwargs: Any) -> List[float]:
        """
        Sinh vector biểu diễn (Embedding) cho văn bản đầu vào.

        Args:
            text: Văn bản cần tạo embedding.
            **kwargs: Tham số bổ sung.

        Returns:
            List[float]: Vector embedding.
        """
        pass

    @abstractmethod
    async def list_models(self) -> List[Dict[str, Any]]:
        """
        Lấy danh sách các model khả dụng từ provider.

        Returns:
            List[Dict[str, Any]]: Danh sách các model và metadata đi kèm.
        """
        pass
