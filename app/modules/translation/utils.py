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


URL_REGEX = re.compile(
    r'^(?:http|ftp)s?://'  # http:// hoặc https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain
    r'localhost|'  # localhost
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ip
    r'(?::\d+)?'  # port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE
)

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', re.IGNORECASE)


def should_skip_translation(text: str) -> bool:
    """Kiểm tra xem chuỗi có phải là URL, Email, hoặc chỉ chứa số/ký tự đặc biệt không cần dịch."""
    stripped = text.strip()
    if not stripped:
        return True
    # URL hoặc Email
    if URL_REGEX.match(stripped) or EMAIL_REGEX.match(stripped):
        return True
    # Chỉ chứa số, khoảng trắng, các ký tự dấu (+ - : , . /)
    if re.match(r'^[0-9\s\-\+\(\)\:\,\.\/]+$', stripped):
        return True
    return False


def preprocess_text(text: str) -> tuple[str, bool]:
    """Tiền xử lý: Chuẩn hóa chữ viết hoa toàn bộ (ALL CAPS) về dạng Capitalized để tránh ảo giác NLLB."""
    stripped = text.strip()
    # Nếu viết hoa toàn bộ và có độ dài thực tế lớn hơn 3 ký tự chữ cái
    if stripped.isupper() and len(re.findall(r'[a-zA-ZÀ-ỹ]', stripped)) > 3:
        # Chuyển về dạng Capitalize (chữ cái đầu viết hoa, còn lại viết thường)
        # NLLB sẽ dịch chuẩn ngữ pháp hơn nhiều
        return stripped.capitalize(), True
    return text, False


def postprocess_text(translated: str, is_all_caps: bool) -> str:
    """Hậu xử lý: Khôi phục định dạng viết hoa toàn bộ nếu câu gốc là viết hoa toàn bộ."""
    if is_all_caps:
        return translated.upper()
    return translated
