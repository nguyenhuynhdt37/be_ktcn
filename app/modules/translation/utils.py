import hashlib
import re
from app.core.config import settings
from app.modules.translation.exceptions import InvalidInputException

# Regex phát hiện các ký tự rác/không hợp lệ (ví dụ: các ký tự điều khiển ASCII không hiển thị)
INVALID_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

def validate_translation_input(text: str) -> None:
    """Validate văn bản đầu vào cho dịch thuật."""
    if not text or not text.strip():
        raise InvalidInputException("Văn bản cần dịch không được để trống")
        
    if len(text) > settings.TRANSLATION_MAX_INPUT_LENGTH:
        raise InvalidInputException(
            message=f"Độ dài văn bản vượt quá giới hạn cho phép ({settings.TRANSLATION_MAX_INPUT_LENGTH} ký tự)",
            details={"length": len(text), "max_length": settings.TRANSLATION_MAX_INPUT_LENGTH}
        )
        
    if INVALID_CHAR_RE.search(text):
        raise InvalidInputException("Văn bản chứa ký tự không hợp lệ hoặc ký tự điều khiển ẩn")

def get_cache_key(text: str, target_lang: str) -> str:
    """Tạo key Redis từ SHA256 của văn bản và ngôn ngữ đích."""
    hashed = hashlib.sha256(text.strip().encode("utf-8")).hexdigest()
    return f"translation:{target_lang}:{hashed}"
