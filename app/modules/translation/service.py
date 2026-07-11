import asyncio
import time
import json
from loguru import logger
import redis.asyncio as aioredis
from typing import Optional

from app.core.config import settings
from app.shared.redis import redis_pool
from app.modules.translation.utils import (
    get_cache_key,
    validate_translation_input,
    should_skip_translation,
    preprocess_text,
    postprocess_text
)
from app.shared.ai.service import AIService
from app.modules.translation.schemas.common import TranslationContext

# Mapping mã ngôn ngữ sang tên ngôn ngữ rõ ràng cho LLM
LANG_MAP = {
    "en": "English",
    "vi": "Vietnamese",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean"
}

# Cấu hình prompt định hướng theo từng ngữ cảnh dịch thuật
CONTEXT_PROMPTS = {
    TranslationContext.MENU_NAME: (
        "Đây là tên của một mục trong menu điều hướng website trường đại học. "
        "Hãy dịch thật ngắn gọn, súc tích, chuyên nghiệp (1-3 từ) và sử dụng thuật ngữ website đại học chuẩn "
        "(ví dụ: 'Giới thiệu' -> 'About', 'Đào tạo' -> 'Academics')."
    ),
    TranslationContext.CATEGORY_NAME: (
        "Đây là tên của một danh mục bài viết/tin tức trên website đại học. "
        "Hãy dịch ngắn gọn, súc tích và trang trọng phục vụ danh mục bài viết."
    ),
    TranslationContext.SHORT_DESCRIPTION: (
        "Đây là một đoạn mô tả ngắn. Hãy dịch trôi chảy, tự nhiên, văn phong trang trọng và giữ đúng nghĩa gốc."
    ),
    TranslationContext.DEPARTMENT_NAME: (
        "Đây là tên của một bộ môn hoặc khoa trong trường đại học. "
        "Hãy dịch chính xác theo thuật ngữ học thuật đại học và không dịch theo nghĩa đen "
        "(ví dụ: 'Bộ môn Khoa học Máy tính' -> 'Department of Computer Science')."
    ),
    TranslationContext.DEPARTMENT_DESCRIPTION: (
        "Đây là phần mô tả giới thiệu về bộ môn/khoa đại học. "
        "Hãy dịch trang trọng, trôi chảy và sử dụng văn phong học thuật chuyên nghiệp."
    ),
    TranslationContext.POSITION_NAME: (
        "Đây là tên chức vụ hoặc chức danh nhân sự đại học. "
        "Hãy dịch chính xác theo danh từ chức danh tiếng Anh đại học chuẩn "
        "(ví dụ: 'Trưởng bộ môn' -> 'Head of Department', 'Giảng viên' -> 'Lecturer')."
    ),
    TranslationContext.POSITION_DESCRIPTION: (
        "Đây là phần mô tả chức năng nhiệm vụ của một chức vụ. "
        "Hãy dịch rõ ràng, trang trọng, sử dụng văn phong nhân sự/hành chính chuyên nghiệp."
    ),
    TranslationContext.ENGLISH_NAME: (
        "Đây là trường điền tên tiếng Anh hoặc tên dịch của một thực thể. "
        "Hãy tối ưu hóa chuyển ngữ chính xác nhất cho các tên riêng học thuật/thực thể."
    ),
    TranslationContext.RESEARCH_DIRECTION: (
        "Đây là hướng nghiên cứu khoa học của giảng viên/nhà nghiên cứu. "
        "Hãy dịch chính xác thuật ngữ chuyên ngành khoa học, kỹ thuật và học thuật "
        "(ví dụ: 'Học máy' -> 'Machine Learning')."
    ),
    TranslationContext.ARTICLE_TITLE: (
        "Đây là tiêu đề bài viết hoặc tin tức. "
        "Hãy dịch hấp dẫn, đúng ngữ pháp tiêu đề tiếng Anh, viết hoa các từ chính (Title Case) đối với tiếng Anh, "
        "và sử dụng văn phong báo chí trang trọng."
    ),
    TranslationContext.ARTICLE_SUMMARY: (
        "Đây là phần tóm tắt của một bài viết/tin tức. "
        "Hãy dịch trôi chảy, tự nhiên và sử dụng văn phong tin tức chuyên nghiệp."
    ),
    TranslationContext.SCIENTIFIC_PROFILE: (
        "Đây là nội dung lý lịch khoa học của giảng viên (dạng HTML). "
        "Hãy dịch chính xác các thuật ngữ học thuật, chức danh giảng viên, tên các bài báo/đề tài nghiên cứu. "
        "BẮT BUỘC giữ nguyên hoàn toàn định dạng và cấu trúc HTML."
    ),
    TranslationContext.ARTICLE_CONTENT: (
        "Đây là nội dung chi tiết của bài viết hoặc tin tức (dạng HTML). "
        "BẮT BUỘC bảo toàn 100% cấu trúc HTML: không thay đổi các thẻ (tag) và thuộc tính của chúng "
        "(bao gồm class, id, style, href, src, data-*). Chỉ dịch phần nội dung văn bản hiển thị (text node). "
        "Sử dụng văn phong báo chí đại học trang trọng."
    ),
    TranslationContext.DEPARTMENT_MISSION: (
        "Đây là phần mô tả sứ mệnh của một khoa/bộ môn đại học. "
        "Hãy dịch trang trọng, tràn đầy cảm hứng, truyền đạt đúng tinh thần giáo dục và học thuật, "
        "và bảo toàn cấu trúc HTML nếu có."
    ),
    TranslationContext.DEPARTMENT_VISION: (
        "Đây là phần mô tả tầm nhìn chiến lược của một khoa/bộ môn đại học. "
        "Hãy dịch trang trọng, hướng tới tương lai, sử dụng thuật ngữ phát triển giáo dục chuẩn, "
        "và bảo toàn cấu trúc HTML nếu có."
    ),
    TranslationContext.DEPARTMENT_HISTORY: (
        "Đây là lịch sử hình thành và phát triển của một khoa/bộ môn đại học. "
        "Hãy dịch rõ ràng, chính xác theo dòng thời gian lịch sử, văn phong trang trọng, "
        "và bảo toàn cấu trúc HTML nếu có."
    ),
    TranslationContext.DEPARTMENT_RESEARCH_OVERVIEW: (
        "Đây là tổng quan định hướng và kết quả nghiên cứu khoa học của khoa/bộ môn. "
        "Hãy dịch chính xác các thuật ngữ học thuật chuyên sâu, công nghệ, hướng nghiên cứu, "
        "và bảo toàn cấu trúc HTML nếu có."
    )
}

class TranslationService:
    """
    Dịch vụ dịch thuật tự động sử dụng OmniRoute Gateway (Gemini-2.5-Flash) qua AIService,
    tối ưu hóa cho môi trường Production.
    """
    def __init__(self):
        self.ai_service = AIService()
        
        # Giữ lại các thuộc tính này để đảm bảo tương thích ngược với Unit Tests hiện tại
        self._is_ready = True
        self._model = "OmniRoute"
        self._tokenizer = "OmniRoute"

    @property
    def model_name(self) -> str:
        """Lấy tên model chat đang hoạt động động từ cấu hình hệ thống."""
        from app.shared.ai.config import get_active_model
        return f"OmniRoute Gateway ({get_active_model()})"

    def load_model(self) -> None:
        """Tương thích ngược: Đăng ký dịch vụ dịch thuật đã sẵn sàng."""
        logger.info("✅ Dịch vụ dịch thuật OmniRoute Gateway đã sẵn sàng.")
        self._is_ready = True

    def warmup(self) -> None:
        """Tương thích ngược: Bỏ qua warmup mô hình local."""
        logger.info("✅ Warmup dịch thuật bỏ qua (sử dụng OmniRoute Gateway).")
        self._is_ready = True

    async def _get_cache(self, text: str, tgt_lang: str, context: Optional[TranslationContext] = None) -> str | None:
        """Lấy bản dịch từ Redis cache."""
        if not redis_pool:
            return None
        try:
            client = aioredis.Redis(connection_pool=redis_pool)
            key = get_cache_key(text, tgt_lang)
            if context:
                key = f"{key}:{context.value}"
            val = await client.get(key)
            if val:
                logger.info(f"🚀 Cache Hit | Ngôn ngữ: {tgt_lang} | Ngữ cảnh: {context.value if context else 'None'} | Số ký tự: {len(text)}")
                return val.decode("utf-8") if isinstance(val, bytes) else val
            logger.info(f"❄️ Cache Miss | Ngôn ngữ: {tgt_lang} | Ngữ cảnh: {context.value if context else 'None'} | Số ký tự: {len(text)}")
        except Exception as e:
            logger.warning(f"Lỗi khi đọc Redis cache: {str(e)}")
        return None

    async def _set_cache(self, text: str, tgt_lang: str, translated: str, context: Optional[TranslationContext] = None) -> None:
        """Lưu bản dịch vào Redis cache."""
        if not redis_pool:
            return
        try:
            client = aioredis.Redis(connection_pool=redis_pool)
            key = get_cache_key(text, tgt_lang)
            if context:
                key = f"{key}:{context.value}"
            await client.setex(key, settings.TRANSLATION_CACHE_TTL, translated)
        except Exception as e:
            logger.warning(f"Lỗi khi lưu Redis cache: {str(e)}")

    async def translate_text(
        self, 
        text: str, 
        target_languages: list[str],
        context: Optional[TranslationContext] = None
    ) -> dict[str, str]:
        """
        API chính dịch một đoạn văn bản tiếng Việt sang danh sách ngôn ngữ đích.
        Có hỗ trợ Redis cache và prompt định hướng theo ngữ cảnh (context).
        """
        validate_translation_input(text)
        
        response = {"vi": text}
        
        # 0. Kiểm tra xem có nên bỏ qua dịch (ví dụ: URL, Email, Số điện thoại)
        if should_skip_translation(text):
            for lang in target_languages:
                response[lang] = text
            return response

        # Tiền xử lý (khử ALL CAPS)
        processed_text, is_all_caps = preprocess_text(text)
        
        for lang in target_languages:
            # 1. Kiểm tra cache với text đã tiền xử lý
            cached = await self._get_cache(processed_text, lang, context)
            if cached is not None:
                response[lang] = postprocess_text(cached, is_all_caps)
                continue
                
            # 2. Gọi AIService dịch qua OmniRoute
            tgt_lang_name = LANG_MAP.get(lang, lang)
            system_instruction = (
                "Bạn là một dịch giả chuyên nghiệp. Hãy dịch văn bản từ tiếng Việt sang ngôn ngữ đích được yêu cầu. "
                "Chỉ trả về kết quả dịch trực tiếp, không giải thích, không thêm bất kỳ ký tự hay lời chào nào khác."
            )
            
            # Bổ sung ngữ cảnh định hướng dịch nếu có
            if context and context in CONTEXT_PROMPTS:
                system_instruction += f"\nNgữ cảnh dịch: {CONTEXT_PROMPTS[context]}"
                
            prompt = f"Dịch văn bản sau sang {tgt_lang_name}:\n{processed_text}"
            
            try:
                translated = await self.ai_service.generate_text(
                    prompt=prompt,
                    system_instruction=system_instruction,
                    temperature=0.0,
                )
                translated = translated.strip()
            except Exception as e:
                logger.error(f"Lỗi khi dịch text qua AIService ({lang}): {e}")
                # Fallback: Trả về bản gốc nếu AI lỗi
                translated = processed_text
            
            # 3. Lưu cache với text đã tiền xử lý
            await self._set_cache(processed_text, lang, translated, context)
            response[lang] = postprocess_text(translated, is_all_caps)
            
        return response

    async def translate_batch(
        self, 
        texts: list[str], 
        target_languages: list[str],
        context: Optional[TranslationContext] = None
    ) -> list[dict[str, str]]:
        """
        API dịch một danh sách đoạn văn bản sang danh sách ngôn ngữ đích (Tối ưu hóa batch).
        Có hỗ trợ Redis cache và prompt định hướng theo ngữ cảnh (context).
        """
        for text in texts:
            validate_translation_input(text)
            
        # Khởi tạo kết quả
        results = [{"vi": text} for text in texts]

        for lang in target_languages:
            # Tìm xem text nào chưa có trong cache để dịch theo batch
            pending_texts = []
            pending_indices = []
            preprocess_info = {}
            
            for idx, text in enumerate(texts):
                # 0. Bỏ qua dịch nếu là URL/Email/Số
                if should_skip_translation(text):
                    results[idx][lang] = text
                    continue
                
                # Tiền xử lý
                processed_text, is_all_caps = preprocess_text(text)
                preprocess_info[idx] = (processed_text, is_all_caps)
                
                # 1. Kiểm tra cache
                cached = await self._get_cache(processed_text, lang, context)
                if cached is not None:
                    results[idx][lang] = postprocess_text(cached, is_all_caps)
                else:
                    pending_texts.append(processed_text)
                    pending_indices.append(idx)
            
            # Nếu có chuỗi cần dịch bằng model
            if pending_texts:
                tgt_lang_name = LANG_MAP.get(lang, lang)
                system_instruction = (
                    "Bạn là dịch giả chuyên nghiệp. Bạn sẽ nhận được một danh sách các chuỗi văn bản tiếng Việt dưới dạng JSON array. "
                    "Hãy dịch chúng sang ngôn ngữ đích và trả về kết quả dưới dạng một JSON array tương ứng có cùng số lượng phần tử và đúng thứ tự. "
                    "Chỉ trả về chuỗi JSON array hợp lệ, không giải thích, không bọc trong ```json."
                )
                
                # Bổ sung ngữ cảnh định hướng dịch nếu có
                if context and context in CONTEXT_PROMPTS:
                    system_instruction += f"\nNgữ cảnh dịch cho tất cả các phần tử: {CONTEXT_PROMPTS[context]}"
                    
                prompt = f"Dịch danh sách các văn bản sau sang {tgt_lang_name}:\n{json.dumps(pending_texts, ensure_ascii=False)}"
                
                try:
                    translated_resp = await self.ai_service.generate_text(
                        prompt=prompt,
                        system_instruction=system_instruction,
                        temperature=0.0,
                    )
                    translated_resp = translated_resp.strip()
                    
                    # Loại bỏ phần bọc ```json và ``` nếu AI vẫn thêm vào
                    if translated_resp.startswith("```"):
                        lines = translated_resp.splitlines()
                        if lines[0].startswith("```"):
                            lines = lines[1:]
                        if lines and lines[-1].startswith("```"):
                            lines = lines[:-1]
                        translated_resp = "\n".join(lines).strip()
                    
                    translated_list = json.loads(translated_resp)
                    if not isinstance(translated_list, list) or len(translated_list) != len(pending_texts):
                        raise ValueError("Số lượng phần tử dịch trả về không khớp.")
                except Exception as e:
                    logger.warning(f"Lỗi khi dịch batch qua AIService ({lang}), tiến hành fallback dịch tuần tự: {e}")
                    # Fallback: dịch từng câu đơn lẻ
                    translated_list = []
                    for p_text in pending_texts:
                        single_prompt = f"Dịch văn bản sau sang {tgt_lang_name}:\n{p_text}"
                        single_instruction = (
                            "Bạn là một dịch giả chuyên nghiệp. Hãy dịch văn bản từ tiếng Việt sang ngôn ngữ đích được yêu cầu. "
                            "Chỉ trả về kết quả dịch trực tiếp, không giải thích, không thêm bất kỳ ký tự hay lời chào nào khác."
                        )
                        if context and context in CONTEXT_PROMPTS:
                            single_instruction += f"\nNgữ cảnh dịch: {CONTEXT_PROMPTS[context]}"
                        try:
                            t_single = await self.ai_service.generate_text(
                                prompt=single_prompt,
                                system_instruction=single_instruction,
                                temperature=0.0,
                            )
                            translated_list.append(t_single.strip())
                        except Exception as ex:
                            logger.error(f"Fallback dịch đơn lẻ thất bại: {ex}")
                            translated_list.append(p_text)
                
                # Lưu cache và map kết quả
                for idx_in_pending, translated in enumerate(translated_list):
                    original_idx = pending_indices[idx_in_pending]
                    processed_text, is_all_caps = preprocess_info[original_idx]
                    
                    await self._set_cache(processed_text, lang, translated, context)
                    results[original_idx][lang] = postprocess_text(translated, is_all_caps)

        return results

    async def translate_html(
        self, 
        html_content: str, 
        target_languages: list[str],
        context: Optional[TranslationContext] = None
    ) -> dict[str, str]:
        """
        API chuyên dụng dịch nội dung HTML (cho CKEditor), giữ nguyên cấu trúc DOM và định dạng.
        Sử dụng OmniRoute Gateway gửi toàn bộ HTML cho LLM dịch trực tiếp để bảo toàn cấu trúc thẻ, class, href, src.
        Có hỗ trợ Redis cache và prompt định hướng theo ngữ cảnh (context).
        """
        if not html_content or not html_content.strip():
            return {lang: html_content for lang in ["vi"] + target_languages}

        # Khởi tạo kết quả
        response = {"vi": html_content}

        for lang in target_languages:
            # 1. Kiểm tra cache cho toàn bộ chuỗi HTML
            cached = await self._get_cache(html_content, lang, context)
            if cached is not None:
                response[lang] = cached
                continue

            tgt_lang_name = LANG_MAP.get(lang, lang)
            system_instruction = (
                "Bạn là dịch giả chuyên nghiệp. Hãy dịch nội dung văn bản của chuỗi HTML sau sang ngôn ngữ đích được yêu cầu. "
                "BẮT BUỘC giữ nguyên hoàn toàn cấu trúc HTML, tất cả các thẻ (như <p>, <a>, <span>, <img>, <table>, <tr>, <td> v.v.) và các thuộc tính của chúng (class, href, src, target, alt). "
                "Chỉ dịch phần văn bản hiển thị. Chỉ trả về chuỗi HTML đã dịch, không giải thích, không bọc trong ```html hoặc ```."
            )
            
            # Bổ sung ngữ cảnh định hướng dịch HTML nếu có
            if context and context in CONTEXT_PROMPTS:
                system_instruction += f"\nNgữ cảnh dịch HTML: {CONTEXT_PROMPTS[context]}"
                
            prompt = f"Dịch chuỗi HTML sau sang {tgt_lang_name}:\n{html_content}"

            try:
                translated = await self.ai_service.generate_text(
                    prompt=prompt,
                    system_instruction=system_instruction,
                    temperature=0.0,
                )
                translated = translated.strip()

                # Loại bỏ phần bọc ```html hoặc ```
                if translated.startswith("```"):
                    lines = translated.splitlines()
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].startswith("```"):
                        lines = lines[:-1]
                    translated = "\n".join(lines).strip()

            except Exception as e:
                logger.error(f"Lỗi khi dịch HTML qua AIService ({lang}): {e}")
                # Fallback: Giữ nguyên HTML gốc nếu lỗi
                translated = html_content

            # 2. Lưu cache cho toàn bộ chuỗi HTML
            await self._set_cache(html_content, lang, translated, context)
            response[lang] = translated

        return response

translation_service = TranslationService()
