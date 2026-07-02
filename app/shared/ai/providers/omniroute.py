import time
import httpx
from typing import Any, Dict, List, Optional
import uuid
from loguru import logger

from app.shared.ai.base import BaseAIProvider
from app.core.database import SessionLocal
from app.modules.ai_hub.models import AIRequestLog


def estimate_cost(model_name: str, prompt_tokens: int, completion_tokens: int) -> float:
    """
    Ước lượng chi phí cuộc gọi dựa trên số lượng token và giá tiền thực tế của nhà cung cấp (trên 1 triệu token).
    """
    pricing = {
        "gemini-2.5-flash": {"input": 0.075, "output": 0.30},
        "llama-3.3-70b": {"input": 0.59, "output": 0.79},
        "cerebras-model": {"input": 0.10, "output": 0.10},
        "mistral-model": {"input": 2.0, "output": 6.0},
        "openrouter-model": {"input": 1.0, "output": 1.0},
        # Embedding models pricing (input only)
        "3-small": {"input": 0.02, "output": 0.0},
        "ada-002": {"input": 0.10, "output": 0.0},
        "zhipu-embedding": {"input": 0.015, "output": 0.0},
        "embedding-model": {"input": 0.02, "output": 0.0},
    }

    # Tìm key khớp gần nhất với model alias
    model_key = None
    for k in pricing.keys():
        if k in model_name.lower():
            model_key = k
            break

    if not model_key:
        return 0.0

    price = pricing[model_key]
    cost = (prompt_tokens * price["input"] + completion_tokens * price["output"]) / 1_000_000
    return cost


def normalize_to_1536_dimensions(vector: list[float]) -> list[float]:
    """
    Chuẩn hóa vector đặc trưng về đúng 1536 chiều bằng thuật toán:
    - Nếu thiếu chiều (N < 1536): Pad thêm các giá trị 0.0 ở cuối.
    - Nếu thừa chiều (N > 1536): Cắt bớt và chuẩn hóa L2 (L2 normalization).
    """
    import math
    current_dim = len(vector)
    if current_dim == 1536:
        return vector

    if current_dim < 1536:
        # Pad thêm 0.0
        return vector + [0.0] * (1536 - current_dim)

    # Truncate cắt bớt
    truncated = vector[:1536]
    # L2 Normalization để đảm bảo tính chuẩn hóa của vector đặc trưng
    sq_sum = sum(x * x for x in truncated)
    if sq_sum > 0:
        norm = math.sqrt(sq_sum)
        return [x / norm for x in truncated]

    return truncated


async def save_log_to_db(
    model: str,
    prompt: str,
    response: Optional[str] = None,
    tokens_prompt: int = 0,
    tokens_completion: int = 0,
    cost: float = 0.0,
    latency_ms: int = 0,
    status: str = "SUCCESS",
    error_message: Optional[str] = None,
    user_id: Optional[uuid.UUID] = None,
    username: Optional[str] = None,
    db_session: Optional[Any] = None,
) -> None:
    """
    Hàm helper lưu log vào Postgres DB sử dụng session được truyền vào hoặc tự tạo mới.
    """
    log_item = AIRequestLog(
        user_id=user_id,
        username=username,
        model=model,
        prompt=prompt,
        response=response,
        tokens_prompt=tokens_prompt,
        tokens_completion=tokens_completion,
        cost=cost,
        latency_ms=latency_ms,
        status=status,
        error_message=error_message,
    )

    async def _insert(session):
        session.add(log_item)
        await session.commit()

    try:
        if db_session:
            # Sử dụng session có sẵn của request hiện tại
            db_session.add(log_item)
            await db_session.commit()
        else:
            # Tạo session mới độc lập (dành cho background tasks/scripts)
            async with SessionLocal() as session:
                await _insert(session)
    except Exception as e:
        logger.error(f"Failed to save AI request log to DB: {e}")


class OmniRouteProvider(BaseAIProvider):
    """
    OmniRoute Provider giao tiếp với OmniRoute Gateway qua giao thức tương thích OpenAI API.
    Đồng thời tự động ghi nhận logs cuộc gọi vào database chính của hệ thống.
    """

    def __init__(self, api_key: str, base_url: str, default_model: Optional[str] = None):
        self.api_key = api_key
        # Đảm bảo base_url kết thúc bằng /v1 nếu cần, hoặc cấu hình chính xác
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model or "gpt-4o"

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        history: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        url = f"{self.base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Trích xuất các tham số logs đặc biệt truyền từ Router (nếu có)
        user_id = kwargs.pop("user_id", None)
        username = kwargs.pop("username", None)
        db_session = kwargs.pop("db", None)

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})

        if history:
            messages.extend(history)

        messages.append({"role": "user", "content": prompt})

        # Cho phép lấy model từ kwargs truyền động, nếu không thì fallback về default_model
        model_to_use = kwargs.pop("model", self.default_model)

        # Trích xuất biến metadata trả ngược nếu có
        response_meta = kwargs.pop("response_meta", None)

        payload = {
            "model": model_to_use,
            "messages": messages,
            "temperature": temperature if temperature is not None else 0.7,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        payload.update(kwargs)

        logger.debug(f"Calling OmniRoute: {url} with model {model_to_use}")

        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]

                # Lấy mô hình thực tế xử lý (có thể khác model_to_use nếu xảy ra fallback)
                actual_model = data.get("model", model_to_use)
                if isinstance(response_meta, dict):
                    response_meta["actual_model"] = actual_model

                # Tính toán thống kê từ response metadata
                latency_ms = int((time.time() - start_time) * 1000)
                usage = data.get("usage", {})
                tokens_prompt = usage.get("prompt_tokens", 0)
                tokens_completion = usage.get("completion_tokens", 0)
                cost = estimate_cost(actual_model, tokens_prompt, tokens_completion)

                # Ghi log thành công vào DB theo mô hình thực tế xử lý
                await save_log_to_db(
                    model=actual_model,
                    prompt=prompt,
                    response=content,
                    tokens_prompt=tokens_prompt,
                    tokens_completion=tokens_completion,
                    cost=cost,
                    latency_ms=latency_ms,
                    status="SUCCESS",
                    user_id=user_id,
                    username=username,
                    db_session=db_session,
                )

                return content

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            if isinstance(e, httpx.HTTPStatusError):
                error_msg = f"HTTP {e.response.status_code}: {e.response.text}"

            # Ghi log thất bại vào DB
            await save_log_to_db(
                model=model_to_use,
                prompt=prompt,
                response=None,
                tokens_prompt=0,
                tokens_completion=0,
                cost=0.0,
                latency_ms=latency_ms,
                status="FAILED",
                error_message=error_msg[:1000],  # Giới hạn độ dài lỗi
                user_id=user_id,
                username=username,
                db_session=db_session,
            )

            logger.error(f"Error calling OmniRoute: {error_msg}")
            raise

    async def generate_embedding(self, text: str, **kwargs: Any) -> List[float]:
        url = f"{self.base_url}/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Trích xuất các tham số logs đặc biệt truyền từ Router (nếu có)
        user_id = kwargs.pop("user_id", None)
        username = kwargs.pop("username", None)
        db_session = kwargs.pop("db", None)
        response_meta = kwargs.pop("response_meta", None)

        model_to_use = kwargs.pop("model", "text-embedding-3-small")

        payload = {
            "input": text,
            "model": model_to_use,
        }
        payload.update(kwargs)

        logger.debug(f"Calling OmniRoute Embeddings: {url} with model {model_to_use}")

        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                embedding = data["data"][0]["embedding"]
                original_len = len(embedding)
                normalized_embedding = normalize_to_1536_dimensions(embedding)

                actual_model = data.get("model", model_to_use)
                if isinstance(response_meta, dict):
                    response_meta["actual_model"] = actual_model

                # Tính toán thống kê
                latency_ms = int((time.time() - start_time) * 1000)
                usage = data.get("usage", {})
                tokens_prompt = usage.get("prompt_tokens", 0)
                cost = estimate_cost(actual_model, tokens_prompt, 0)

                # Ghi log thành công vào DB
                await save_log_to_db(
                    model=actual_model,
                    prompt=text,
                    response=f"[Vector Embedding {original_len} dimensions -> Normalized to {len(normalized_embedding)}]",
                    tokens_prompt=tokens_prompt,
                    tokens_completion=0,
                    cost=cost,
                    latency_ms=latency_ms,
                    status="SUCCESS",
                    user_id=user_id,
                    username=username,
                    db_session=db_session,
                )

                return normalized_embedding

        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            if isinstance(e, httpx.HTTPStatusError):
                error_msg = f"HTTP {e.response.status_code}: {e.response.text}"

            # Ghi log thất bại vào DB
            await save_log_to_db(
                model=model_to_use,
                prompt=text,
                response=None,
                tokens_prompt=0,
                tokens_completion=0,
                cost=0.0,
                latency_ms=latency_ms,
                status="FAILED",
                error_message=error_msg[:1000],
                user_id=user_id,
                username=username,
                db_session=db_session,
            )

            logger.error(f"Error calling OmniRoute Embedding: {error_msg}")
            raise

    async def list_models(self) -> List[Dict[str, Any]]:
        """
        Gọi endpoint /v1/models của OmniRoute để lấy danh sách các model.
        """
        url = f"{self.base_url}/v1/models"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }
        logger.debug(f"Calling OmniRoute List Models: {url}")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                return data.get("data", [])
        except Exception as e:
            logger.error(f"Error fetching models from OmniRoute: {e}")
            return []
