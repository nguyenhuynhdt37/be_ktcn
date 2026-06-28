import base64
import hashlib
from cryptography.fernet import Fernet
from app.core.config import settings


def _get_fernet() -> Fernet:
    """Tạo khóa mã hóa 32-byte hợp lệ từ SECRET_KEY của ứng dụng."""
    key_bytes = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(fernet_key)


def encrypt_data(data: str) -> str:
    """Mã hóa chuỗi dữ liệu nhạy cảm."""
    if not data:
        return ""
    f = _get_fernet()
    return f.encrypt(data.encode()).decode()


def decrypt_data(token: str) -> str:
    """Giải mã chuỗi dữ liệu nhạy cảm."""
    if not token:
        return ""
    f = _get_fernet()
    try:
        return f.decrypt(token.encode()).decode()
    except Exception:
        # Nếu giải mã thất bại (VD: đổi SECRET_KEY), trả về rỗng để tránh crash hệ thống
        return ""
