import re
import httpx
from loguru import logger
from app.core.exceptions import BadRequestException
from app.modules.ai.providers import GeminiProvider


class GeminiModelDiscoveryService:
    """Service chịu trách nhiệm tự động phát hiện, phân loại, sắp xếp và kiểm tra tính khả dụng của các model Gemini."""

    @staticmethod
    def get_model_priority(model_name: str) -> tuple[float, int]:
        """
        Tính điểm ưu tiên cho model Gemini:
        1. Thế hệ (2.5 > 2.0 > 1.5)
        2. Loại model (Flash > Pro > Ultra > Khác)
        """
        model_name_lower = model_name.lower()
        
        # 1. Trích xuất version thế hệ
        generation = 1.0
        match = re.search(r"gemini-(\d+\.\d+)", model_name_lower)
        if match:
            generation = float(match.group(1))
        else:
            match_int = re.search(r"gemini-(\d+)", model_name_lower)
            if match_int:
                generation = float(match_int.group(1))
                
        # 2. Xác định loại model
        type_weight = 0
        if "flash" in model_name_lower:
            type_weight = 3  # Ưu tiên Flash nhất
        elif "pro" in model_name_lower:
            type_weight = 2
        elif "ultra" in model_name_lower:
            type_weight = 1
            
        return (generation, type_weight)

    async def discover_and_select_active_model(
        self, api_key: str, setting_type: str = "text", base_url: str | None = None, timeout: int = 10
    ) -> tuple[str, list[str], list[dict]]:
        """
        Thực hiện toàn bộ luồng tự động phát hiện và kiểm tra model hoạt động của một loại cụ thể.
        Trả về tuple: (model_hoạt_động_đầu_tiên, danh_sách_sorted_models_khả_dụng, usage_records)
        """
        # 1. Gọi API lấy toàn bộ models khả dụng
        url = "https://generativelanguage.googleapis.com/v1beta/models"
        headers = {
            "x-goog-api-key": api_key
        }
        
        logger.info("Đang gọi Google API để lấy danh sách models khả dụng...")
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.get(url, headers=headers)
                if response.status_code != 200:
                    logger.error(f"Gemini API return error status: {response.status_code}, response: {response.text}")
                    raise BadRequestException(
                        message=f"API Key Gemini không hoạt động hoặc không có quyền truy cập API (Mã lỗi HTTP: {response.status_code})."
                    )
                
                data = response.json()
            except httpx.TimeoutException:
                raise BadRequestException(message="Yêu cầu kết nối tới Google API để lấy danh sách model bị Timeout.")
            except Exception as e:
                if isinstance(e, BadRequestException):
                    raise e
                raise BadRequestException(message=f"Không thể kết nối tới Google API để lấy danh sách model: {str(e)}")

        models_list = data.get("models", [])
        logger.info(f"Phát hiện tổng cộng {len(models_list)} models từ API Key của Google.")

        provider = GeminiProvider()
        usage_records = []
        active_model = None

        if setting_type == "text":
            # Lọc model sinh văn bản
            valid_models = []
            for m in models_list:
                m_name = m.get("name", "").replace("models/", "")
                supported_methods = m.get("supportedGenerationMethods", [])
                
                if "generateContent" in supported_methods:
                    m_name_lower = m_name.lower()
                    exclude_keywords = [
                        "embed", "embedding", "aqa", "speech", "bidi", "imagen", 
                        "translation", "tuning", "tts", "audio", "voice", "image", "video"
                    ]
                    if not any(x in m_name_lower for x in exclude_keywords):
                        valid_models.append(m_name)

            logger.info(f"Danh sách models sau khi lọc sinh nội dung (còn {len(valid_models)}): {valid_models}")
            if not valid_models:
                raise BadRequestException(
                    message="API Key hợp lệ nhưng không tìm thấy model Gemini sinh nội dung nào khả dụng cho tài khoản này."
                )

            sorted_models = sorted(valid_models, key=self.get_model_priority, reverse=True)
            logger.info(f"Danh sách models sau khi sắp xếp theo thứ tự ưu tiên: {sorted_models}")

            system_instruction = "You are a connectivity test assistant. Respond in JSON format."
            prompt = "Return a JSON object with a single key 'status' and value 'OK'."

            for model in sorted_models:
                logger.info(f"Đang kiểm tra khả năng hoạt động của model: {model}...")
                try:
                    _, p_tokens, c_tokens = await provider.generate_response(
                        prompt=prompt,
                        system_instruction=system_instruction,
                        model=model,
                        api_key=api_key,
                        base_url=base_url,
                        temperature=0.0,
                        max_tokens=10,
                        timeout=timeout
                    )
                    usage_records.append({
                        "model": model,
                        "prompt_tokens": p_tokens,
                        "completion_tokens": c_tokens
                    })
                    active_model = model
                    logger.info(f"✨ Model '{model}' hoạt động tốt và được lựa chọn làm model mặc định!")
                    break
                except Exception as e:
                    logger.warning(f"❌ Model '{model}' kiểm tra thất bại. Chi tiết: {str(e)}")
                    usage_records.append({
                        "model": model,
                        "prompt_tokens": 0,
                        "completion_tokens": 0
                    })
                    continue

            if not active_model:
                raise BadRequestException(
                    message="API Key hợp lệ nhưng không có model Gemini sinh văn bản nào khả dụng. Nguyên nhân có thể do quota, quyền truy cập hoặc billing."
                )
            
            return active_model, sorted_models, usage_records

        elif setting_type == "embedding":
            # Lọc model embedding
            valid_embedding_models = []
            for m in models_list:
                m_name = m.get("name", "").replace("models/", "")
                supported_methods = m.get("supportedGenerationMethods", [])
                
                if "embedContent" in supported_methods:
                    if "embed" in m_name.lower():
                        valid_embedding_models.append(m_name)

            logger.info(f"Danh sách models embedding phát hiện được (còn {len(valid_embedding_models)}): {valid_embedding_models}")
            if not valid_embedding_models:
                raise BadRequestException(
                    message="API Key hợp lệ nhưng không tìm thấy model Gemini Embedding nào khả dụng cho tài khoản này."
                )

            sorted_embedding_models = sorted(valid_embedding_models, reverse=True)
            logger.info(f"Danh sách models embedding sau khi sắp xếp: {sorted_embedding_models}")

            for model in sorted_embedding_models:
                logger.info(f"Đang kiểm tra khả năng hoạt động của model embedding: {model}...")
                try:
                    _, emb_tokens = await provider.embed_content(
                        text="Hello",
                        model=model,
                        api_key=api_key,
                        base_url=base_url,
                        timeout=timeout
                    )
                    usage_records.append({
                        "model": model,
                        "prompt_tokens": emb_tokens,
                        "completion_tokens": 0
                    })
                    active_model = model
                    logger.info(f"✨ Model embedding '{model}' hoạt động tốt và được lựa chọn làm mặc định!")
                    break
                except Exception as e:
                    logger.warning(f"❌ Model embedding '{model}' kiểm tra thất bại. Chi tiết: {str(e)}")
                    usage_records.append({
                        "model": model,
                        "prompt_tokens": 0,
                        "completion_tokens": 0
                    })
                    continue

            if not active_model:
                active_model = "text-embedding-004"
                logger.warning("Không có model embedding nào phản hồi thành công. Sử dụng 'text-embedding-004' làm fallback.")
            
            return active_model, sorted_embedding_models, usage_records

        else:
            raise BadRequestException(message=f"Loại cấu hình không hợp lệ: {setting_type}")
