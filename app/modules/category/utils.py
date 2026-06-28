import re
import unicodedata


def generate_slug(text: str) -> str:
    """
    Chuẩn hóa chuỗi ký tự Tiếng Việt và các ký tự đặc biệt thành Slug hợp lệ cho SEO.
    Ví dụ: "Tin tức tuyển sinh năm 2026!" -> "tin-tuc-tuyen-sinh-nam-2026"
    """
    if not text:
        return ""

    # 1. Chuyển chữ hoa thành chữ thường
    text = text.lower()

    # 2. Thay thế ký tự đ/Đ
    text = text.replace("đ", "d")

    # 3. Phân tách tổ hợp dấu bằng NFD
    text = unicodedata.normalize("NFD", text)
    
    # 4. Loại bỏ các ký tự dấu (Combining Diacritical Marks)
    text = "".join(c for c in text if not unicodedata.combining(c))

    # 5. Loại bỏ ký tự đặc biệt (chỉ giữ lại a-z, 0-9, khoảng trắng, gạch ngang)
    text = re.sub(r"[^a-z0-9\s-]", "", text)

    # 6. Thay thế khoảng trắng và gạch ngang liên tiếp thành một dấu gạch ngang
    text = re.sub(r"[\s-]+", "-", text)

    # 7. Loại bỏ gạch ngang ở đầu và cuối
    text = text.strip("-")

    return text
