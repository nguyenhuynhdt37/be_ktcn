import json
import re
import httpx
from loguru import logger

from app.core.exceptions import BadRequestException


def clean_json_response(text: str) -> str:
    """
    Tách chuỗi JSON sạch ra từ phản hồi của LLM.
    Xử lý trường hợp LLM tự ý bọc kết quả trong block ```json ... ```
    """
    text = text.strip()
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text


class BaseAIProvider:
    """Lớp cơ sở đại diện cho một nhà cung cấp AI."""
    
    async def generate_response(
        self, 
        prompt: str, 
        system_instruction: str, 
        model: str,
        api_key: str,
        base_url: str | None,
        temperature: float,
        max_tokens: int,
        timeout: int
    ) -> tuple[str, int, int]:
        """
        Gửi yêu cầu tới AI model.
        Trả về tuple: (text_phản_hồi, prompt_tokens, completion_tokens)
        """
        raise NotImplementedError

    async def detect_models(self, api_key: str, base_url: str | None, timeout: int) -> list[str]:
        """Trả về danh sách các model khả dụng từ nhà cung cấp."""
        raise NotImplementedError


class GeminiProvider(BaseAIProvider):
    """Implement kết nối tới Google Gemini REST API."""

    async def generate_response(
        self, prompt: str, system_instruction: str, model: str, api_key: str,
        base_url: str | None, temperature: float, max_tokens: int, timeout: int
    ) -> tuple[str, int, int]:
        model_name = model if model.startswith("models/") else f"models/{model}"
        url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent"
        
        headers = {
            "x-goog-api-key": api_key,
            "Content-Type": "application/json"
        }

        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "systemInstruction": {
                "parts": [{"text": system_instruction}]
            },
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "responseMimeType": "application/json"
            }
        }

        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code != 200:
                    logger.error(f"Gemini error response: {response.text}")
                    try:
                        err_json = response.json()
                        err_msg = err_json["error"]["message"]
                        raise BadRequestException(message=f"Lỗi API Gemini ({response.status_code}): {err_msg}")
                    except Exception:
                        raise BadRequestException(message=f"Lỗi kết nối Gemini API: {response.status_code}")
                result = response.json()
                if "error" in result:
                    err_msg = result["error"].get("message", "Unknown error")
                    raise BadRequestException(message=f"Lỗi từ Gemini API: {err_msg}")

                candidates = result.get("candidates", [])
                if not candidates:
                    prompt_feedback = result.get("promptFeedback", {})
                    if prompt_feedback:
                        block_reason = prompt_feedback.get("blockReason", "Unknown")
                        raise BadRequestException(message=f"Yêu cầu bị chặn bởi Gemini. Lý do: {block_reason}")
                    raise BadRequestException(message=f"Không nhận được câu trả lời từ Gemini. Phản hồi thô: {result}")

                candidate = candidates[0]
                content_obj = candidate.get("content", {})
                parts = content_obj.get("parts", [])
                if not parts:
                    finish_reason = candidate.get("finishReason", "UNKNOWN")
                    raise BadRequestException(message=f"Không thể lấy nội dung phản hồi từ Gemini. Lý do kết thúc: {finish_reason}")

                content = parts[0].get("text", "")
                
                # Trích xuất Token Usage
                usage = result.get("usageMetadata", {})
                prompt_tokens = usage.get("promptTokenCount", 0)
                completion_tokens = usage.get("candidatesTokenCount", 0)
                
                return content, prompt_tokens, completion_tokens
            except httpx.TimeoutException:
                logger.error("Timeout when connecting to Gemini API")
                raise BadRequestException(message="Yêu cầu kết nối AI vượt quá thời gian phản hồi (Timeout)")
            except Exception as e:
                if isinstance(e, BadRequestException):
                    raise e
                logger.exception(f"Unhandled error in GeminiProvider: {str(e)}")
                raise BadRequestException(message=f"Không thể kết nối dịch vụ AI. Chi tiết: {str(e)}")

    async def embed_content(
        self, text: str, model: str, api_key: str, base_url: str | None, timeout: int
    ) -> tuple[list[float], int]:
        """Gọi API embedding của Gemini."""
        model_name = model if model.startswith("models/") else f"models/{model}"
        url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:embedContent"
        
        headers = {
            "x-goog-api-key": api_key,
            "Content-Type": "application/json"
        }

        payload = {
            "content": {
                "parts": [{"text": text}]
            }
        }

        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code != 200:
                    logger.error(f"Gemini embedding error response: {response.text}")
                    try:
                        err_json = response.json()
                        err_msg = err_json["error"]["message"]
                        raise BadRequestException(message=f"Lỗi API Gemini Embedding ({response.status_code}): {err_msg}")
                    except Exception:
                        raise BadRequestException(message=f"Lỗi kết nối Gemini Embedding API: {response.status_code}")
                
                result = response.json()
                if "error" in result:
                    err_msg = result["error"].get("message", "Unknown error")
                    raise BadRequestException(message=f"Lỗi từ Gemini Embedding API: {err_msg}")

                embedding_obj = result.get("embedding", {})
                values = embedding_obj.get("values", [])
                prompt_tokens = max(1, len(text) // 4)
                return values, prompt_tokens
            except httpx.TimeoutException:
                logger.error("Timeout when connecting to Gemini Embedding API")
                raise BadRequestException(message="Yêu cầu kết nối AI Embedding vượt quá thời gian phản hồi (Timeout)")
            except Exception as e:
                if isinstance(e, BadRequestException):
                    raise e
                logger.exception(f"Unhandled error in GeminiProvider.embed_content: {str(e)}")
                raise BadRequestException(message=f"Không thể kết nối dịch vụ AI Embedding. Chi tiết: {str(e)}")

    async def detect_models(self, api_key: str, base_url: str | None, timeout: int) -> list[str]:
        url = "https://generativelanguage.googleapis.com/v1beta/models"
        headers = {
            "x-goog-api-key": api_key
        }
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.get(url, headers=headers)
                if response.status_code != 200:
                    logger.error(f"Gemini models API error: {response.text}")
                    try:
                        err_json = response.json()
                        err_msg = err_json["error"]["message"]
                        raise BadRequestException(message=f"API Key Gemini không hoạt động hoặc không hợp lệ ({response.status_code}): {err_msg}")
                    except Exception:
                        raise BadRequestException(message=f"API Key Gemini không hoạt động hoặc không hợp lệ: {response.status_code}")
                data = response.json()
                filtered_models = []
                for m in data.get("models", []):
                    methods = m.get("supportedGenerationMethods", [])
                    if "generateContent" in methods:
                        name = m["name"].replace("models/", "")
                        filtered_models.append(name)
                return sorted(list(set(filtered_models)))
            except Exception as e:
                if isinstance(e, BadRequestException):
                    raise e
                logger.exception(f"Error fetching Gemini models: {str(e)}")
                raise BadRequestException(message=f"Không thể lấy danh sách model Gemini: {str(e)}")


class AIFactory:
    """Lớp quản lý khởi tạo các Provider."""

    @staticmethod
    def get_provider(provider_name: str) -> BaseAIProvider:
        p_name = provider_name.lower()
        if p_name == "gemini":
            return GeminiProvider()
        else:
            raise BadRequestException(
                message=f"Hệ thống chỉ hỗ trợ Google Gemini. Provider '{provider_name}' không được phép.",
                error_code="UNSUPPORTED_AI_PROVIDER"
            )
