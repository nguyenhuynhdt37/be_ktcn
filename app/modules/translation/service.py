import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from loguru import logger
import redis.asyncio as aioredis

from app.core.config import settings
from app.shared.redis import redis_pool
from app.modules.translation.exceptions import ModelNotReadyException
from app.modules.translation.utils import (
    get_cache_key,
    validate_translation_input,
    should_skip_translation,
    preprocess_text,
    postprocess_text
)

# NLLB-200 Language Mapping
NLLB_LANG_MAP = {
    "vi": "vie_Latn",
    "en": "eng_Latn"
}

class TranslationService:
    """
    Dịch vụ dịch thuật tự động sử dụng NLLB-200, tối ưu hóa cho môi trường Production.
    """
    def __init__(self):
        self.model_name = settings.TRANSLATION_MODEL_NAME
        
        # Tự động nhận diện thiết bị tốt nhất (CUDA > MPS > CPU) trừ khi ép buộc chạy cpu
        import torch
        configured_device = settings.TRANSLATION_DEVICE
        if configured_device == "cpu":
            self.device = "cpu"
        else:
            if torch.cuda.is_available():
                self.device = "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                self.device = "mps"
            else:
                self.device = "cpu"

        self._tokenizer = None
        self._model = None
        self._translator = None
        self._is_ready = False
        # Giới hạn 1 worker để tránh quá tải CPU khi dịch song song
        self._executor = ThreadPoolExecutor(max_workers=1)

    def load_model(self) -> None:
        """Tải mô hình vào RAM và chuẩn bị Tokenizer và Model."""
        if self._is_ready:
            return
            
        start_time = time.time()
        logger.info(f"⏳ Bắt đầu tải mô hình NLLB-200 ({self.model_name}) lên {self.device}...")
        
        import torch
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name, src_lang="vie_Latn", local_files_only=True)
        self._model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name, local_files_only=True)
        
        # Chuyển thiết bị
        if self.device != "cpu":
            self._model = self._model.to(self.device)
            
        load_duration = time.time() - start_time
        logger.info(f"✅ Đã tải mô hình thành công! Thời gian tải: {load_duration:.2f} giây.")
        self._is_ready = True

    def warmup(self) -> None:
        """Thực hiện warmup mô hình để sẵn sàng dịch nhanh."""
        self.load_model()
        logger.info("⏳ Đang thực hiện warmup mô hình dịch thuật...")
        import torch
        
        start_time = time.time()
        with torch.inference_mode():
            # Dịch thử
            inputs = self._tokenizer("Xin chào", return_tensors="pt")
            if self.device != "cpu":
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            translated_tokens = self._model.generate(
                **inputs,
                forced_bos_token_id=self._tokenizer.convert_tokens_to_ids("eng_Latn"),
                max_length=20
            )
            self._tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)
            
        duration = time.time() - start_time
        logger.info(f"✅ Warmup hoàn tất! Thời gian warmup: {duration:.2f} giây. Mô hình sẵn sàng phục vụ!")

    def _translate_single_sync(self, text: str, tgt_lang: str) -> str:
        """Dịch đồng bộ một chuỗi (chạy trong thread pool)."""
        if not self._is_ready:
            raise ModelNotReadyException()
            
        import torch
        tgt_nllb = NLLB_LANG_MAP.get(tgt_lang)
        if not tgt_nllb:
            raise ValueError(f"Ngôn ngữ không được hỗ trợ: {tgt_lang}")
            
        start_time = time.time()
        with torch.inference_mode():
            inputs = self._tokenizer(text, return_tensors="pt")
            if self.device != "cpu":
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                
            translated_tokens = self._model.generate(
                **inputs,
                forced_bos_token_id=self._tokenizer.convert_tokens_to_ids(tgt_nllb),
                max_length=settings.TRANSLATION_MAX_INPUT_LENGTH
            )
            
            result = self._tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)
            
        duration = time.time() - start_time
        logger.info(f"📊 Dịch thành công: {len(text)} ký tự | Thời gian: {duration:.4f} giây | Ngôn ngữ đích: {tgt_lang}")
        return result[0]

    def _translate_batch_sync(self, texts: list[str], tgt_lang: str) -> list[str]:
        """Dịch đồng bộ một mảng chuỗi (chạy trong thread pool)."""
        if not self._is_ready:
            raise ModelNotReadyException()
            
        import torch
        tgt_nllb = NLLB_LANG_MAP.get(tgt_lang)
        if not tgt_nllb:
            raise ValueError(f"Ngôn ngữ không được hỗ trợ: {tgt_lang}")
            
        total_chars = sum(len(t) for t in texts)
        start_time = time.time()
        with torch.inference_mode():
            inputs = self._tokenizer(texts, return_tensors="pt", padding=True)
            if self.device != "cpu":
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                
            translated_tokens = self._model.generate(
                **inputs,
                forced_bos_token_id=self._tokenizer.convert_tokens_to_ids(tgt_nllb),
                max_length=settings.TRANSLATION_MAX_INPUT_LENGTH
            )
            
            results = self._tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)
            
        duration = time.time() - start_time
        logger.info(f"📊 Dịch Batch thành công: {len(texts)} chuỗi, tổng {total_chars} ký tự | Thời gian: {duration:.4f} giây | Ngôn ngữ đích: {tgt_lang}")
        return results

    async def _get_cache(self, text: str, tgt_lang: str) -> str | None:
        """Lấy bản dịch từ Redis cache."""
        if not redis_pool:
            return None
        try:
            client = aioredis.Redis(connection_pool=redis_pool)
            key = get_cache_key(text, tgt_lang)
            val = await client.get(key)
            if val:
                logger.info(f"🚀 Cache Hit | Ngôn ngữ: {tgt_lang} | Số ký tự: {len(text)}")
                return val
            logger.info(f"❄️ Cache Miss | Ngôn ngữ: {tgt_lang} | Số ký tự: {len(text)}")
        except Exception as e:
            logger.warning(f"Lỗi khi đọc Redis cache: {str(e)}")
        return None

    async def _set_cache(self, text: str, tgt_lang: str, translated: str) -> None:
        """Lưu bản dịch vào Redis cache."""
        if not redis_pool:
            return
        try:
            client = aioredis.Redis(connection_pool=redis_pool)
            key = get_cache_key(text, tgt_lang)
            await client.setex(key, settings.TRANSLATION_CACHE_TTL, translated)
        except Exception as e:
            logger.warning(f"Lỗi khi lưu Redis cache: {str(e)}")

    async def translate_text(self, text: str, target_languages: list[str]) -> dict[str, str]:
        """
        API chính dịch một đoạn văn bản tiếng Việt sang danh sách ngôn ngữ đích.
        Có hỗ trợ Redis cache.
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
        loop = asyncio.get_running_loop()
        
        for lang in target_languages:
            # 1. Kiểm tra cache với text đã tiền xử lý
            cached = await self._get_cache(processed_text, lang)
            if cached is not None:
                response[lang] = postprocess_text(cached, is_all_caps)
                continue
                
            # 2. Chạy model dịch trong ThreadPoolExecutor để tránh block event loop
            translated = await loop.run_in_executor(
                self._executor, self._translate_single_sync, processed_text, lang
            )
            
            # 3. Lưu cache với text đã tiền xử lý
            await self._set_cache(processed_text, lang, translated)
            response[lang] = postprocess_text(translated, is_all_caps)
            
        return response

    async def translate_batch(self, texts: list[str], target_languages: list[str]) -> list[dict[str, str]]:
        """
        API dịch một danh sách đoạn văn bản sang danh sách ngôn ngữ đích (Tối ưu hóa batch).
        Có hỗ trợ Redis cache.
        """
        for text in texts:
            validate_translation_input(text)
            
        # Khởi tạo kết quả
        results = [{"vi": text} for text in texts]
        loop = asyncio.get_running_loop()

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
                cached = await self._get_cache(processed_text, lang)
                if cached is not None:
                    results[idx][lang] = postprocess_text(cached, is_all_caps)
                else:
                    pending_texts.append(processed_text)
                    pending_indices.append(idx)
            
            # Nếu có chuỗi cần dịch bằng model
            if pending_texts:
                translated_list = await loop.run_in_executor(
                    self._executor, self._translate_batch_sync, pending_texts, lang
                )
                
                # Lưu cache và map kết quả
                for idx_in_pending, translated in enumerate(translated_list):
                    original_idx = pending_indices[idx_in_pending]
                    processed_text, is_all_caps = preprocess_info[original_idx]
                    
                    await self._set_cache(processed_text, lang, translated)
                    results[original_idx][lang] = postprocess_text(translated, is_all_caps)

        return results

    async def translate_html(self, html_content: str, target_languages: list[str]) -> dict[str, str]:
        """
        API chuyên dụng dịch nội dung HTML (cho CKEditor), giữ nguyên cấu trúc DOM và định dạng.
        Tự động bóc tách ở cấp độ Block văn bản, sử dụng placeholders bảo toàn thẻ inline (bold, italic, links, span...),
        dịch batch tối ưu qua Redis cache và NLLB-200, sau đó khôi phục lại cấu trúc.
        """
        if not html_content or not html_content.strip():
            return {lang: html_content for lang in ["vi"] + target_languages}

        from bs4 import BeautifulSoup
        import re
        
        BLOCK_TAGS = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "td", "th", "div", "section", "article", "caption", "blockquote"}
        INLINE_TAGS = {"b", "strong", "i", "em", "u", "span", "a", "code", "sub", "sup", "small"}

        # Khởi tạo kết quả
        response = {"vi": html_content}

        for lang in target_languages:
            # Dựng cây DOM
            soup = BeautifulSoup(html_content, "html.parser")
            
            # 1. Thu thập các text blocks độc lập (leaf blocks chứa text trực tiếp)
            text_blocks = []
            
            def collect_text_blocks(element):
                if not hasattr(element, "name"):
                    return
                if element.name in ["script", "style"]:
                    return
                    
                is_leaf_block = False
                if element.name in BLOCK_TAGS:
                    has_block_child = any(
                        child.name in BLOCK_TAGS 
                        for child in element.find_all(recursive=True) 
                        if hasattr(child, "name")
                    )
                    if not has_block_child:
                        is_leaf_block = True
                        
                if is_leaf_block:
                    if element.get_text(strip=True):
                        text_blocks.append(element)
                else:
                    for child in element.children:
                        if hasattr(child, "children"):
                            collect_text_blocks(child)
            
            collect_text_blocks(soup)
            if not text_blocks and soup.get_text(strip=True):
                text_blocks = [soup]

            if not text_blocks:
                response[lang] = html_content
                continue

            # 2. Xây dựng placeholders cho các thẻ inline trong từng block
            block_data = [] # List of tuples: (block_element, placeholders_dict, raw_text_with_placeholders)
            
            for block in text_blocks:
                inline_elements = block.find_all(INLINE_TAGS, recursive=True)
                placeholders = {}
                
                # Thay thế từ trong ra ngoài (reversed) để xử lý hoàn hảo tag lồng nhau
                for idx, element in enumerate(reversed(inline_elements)):
                    placeholder_idx = len(inline_elements) - 1 - idx
                    placeholder_open = f" 99910{placeholder_idx} "
                    placeholder_close = f" 99920{placeholder_idx} "
                    
                    placeholders[placeholder_idx] = {
                        "name": element.name,
                        "attrs": element.attrs,
                        "inner_html": element.decode_contents()
                    }
                    
                    new_text = f"{placeholder_open}{element.decode_contents()}{placeholder_close}"
                    element.replace_with(new_text)
                
                # Lấy text thô chứa placeholders
                raw_text = block.get_text()
                block_data.append((block, placeholders, raw_text))

            # 3. Gom danh sách text thô để dịch theo batch tối ưu hiệu năng
            raw_texts = [data[2] for data in block_data]
            translated_results = await self.translate_batch(raw_texts, [lang])

            # 4. Khôi phục thẻ inline và cập nhật lại cây DOM
            for idx, (block, placeholders, _) in enumerate(block_data):
                translated_text = translated_results[idx].get(lang, block.get_text())
                
                # Khôi phục các thẻ inline từ ngoài vào trong
                for p_idx in sorted(placeholders.keys()):
                    info = placeholders[p_idx]
                    
                    # Xây dựng thẻ mở và thẻ đóng gốc
                    attrs_str = ""
                    for k, v in info["attrs"].items():
                        if isinstance(v, list):
                            v_str = " ".join(v)
                        else:
                            v_str = str(v)
                        attrs_str += f' {k}="{v_str}"'
                    
                    tag_open_html = f"<{info['name']}{attrs_str}>"
                    tag_close_html = f"</{info['name']}>"
                    
                    # Khôi phục độc lập thẻ mở và thẻ đóng (giúp chống lỗi xáo trộn cấu trúc)
                    # Loại bỏ khoảng trắng thừa xung quanh placeholder số nếu có
                    translated_text = re.sub(
                        r"\s*99910" + str(p_idx) + r"\s*", 
                        lambda m: tag_open_html, 
                        translated_text,
                        count=1
                    )
                    translated_text = re.sub(
                        r"\s*99920" + str(p_idx) + r"\s*", 
                        lambda m: tag_close_html, 
                        translated_text,
                        count=1
                    )
                
                # Lắp lại HTML đã khôi phục vào block
                block.clear()
                parsed_content = BeautifulSoup(translated_text, "html.parser")
                block.append(parsed_content)

            # Xuất chuỗi HTML hoàn chỉnh đã dịch
            # decode_contents() giúp loại bỏ thẻ bao ngoài nếu soup là block duy nhất
            if len(text_blocks) == 1 and text_blocks[0] == soup:
                response[lang] = soup.decode_contents()
            else:
                response[lang] = str(soup)

        return response


translation_service = TranslationService()
