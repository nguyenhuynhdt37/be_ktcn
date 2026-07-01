import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from loguru import logger
import redis.asyncio as aioredis

from app.core.config import settings
from app.shared.redis import redis_pool
from app.modules.translation.exceptions import ModelNotReadyException
from app.modules.translation.utils import get_cache_key, validate_translation_input

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
        self.device = settings.TRANSLATION_DEVICE
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
        if self.device != "cpu" and torch.cuda.is_available():
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
            if self.device != "cpu" and torch.cuda.is_available():
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
            if self.device != "cpu" and torch.cuda.is_available():
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
            if self.device != "cpu" and torch.cuda.is_available():
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
        loop = asyncio.get_running_loop()
        
        for lang in target_languages:
            # 1. Kiểm tra cache
            cached = await self._get_cache(text, lang)
            if cached is not None:
                response[lang] = cached
                continue
                
            # 2. Chạy model dịch trong ThreadPoolExecutor để tránh block event loop
            translated = await loop.run_in_executor(
                self._executor, self._translate_single_sync, text, lang
            )
            
            # 3. Lưu cache
            await self._set_cache(text, lang, translated)
            response[lang] = translated
            
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
            
            for idx, text in enumerate(texts):
                cached = await self._get_cache(text, lang)
                if cached is not None:
                    results[idx][lang] = cached
                else:
                    pending_texts.append(text)
                    pending_indices.append(idx)
            
            # Nếu có chuỗi cần dịch bằng model
            if pending_texts:
                translated_list = await loop.run_in_executor(
                    self._executor, self._translate_batch_sync, pending_texts, lang
                )
                
                # Lưu cache và map kết quả
                for idx_in_pending, translated in enumerate(translated_list):
                    original_idx = pending_indices[idx_in_pending]
                    original_text = pending_texts[idx_in_pending]
                    
                    await self._set_cache(original_text, lang, translated)
                    results[original_idx][lang] = translated

        return results

translation_service = TranslationService()
