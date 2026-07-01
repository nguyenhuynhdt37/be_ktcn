import uuid
from typing import Optional
from fastapi import Request

def get_locale_from_request(
    request: Request,
    lang_param: Optional[str] = None,
    language_param: Optional[str] = None
) -> str:
    """
    Tự động phân giải ngôn ngữ của request theo thứ tự ưu tiên:
    1. Query Parameter `lang`
    2. Query Parameter `language`
    3. Header `Accept-Language`
    4. Fallback mặc định: "vi" (tiếng Việt)
    """
    # 1. Ưu tiên Query Parameter
    if lang_param and lang_param.strip():
        return lang_param.strip().lower()
    if language_param and language_param.strip():
        return language_param.strip().lower()

    # 2. Đọc từ Accept-Language Header
    accept_lang = request.headers.get("accept-language")
    if accept_lang:
        # Ví dụ: "en-US,en;q=0.9,vi;q=0.8" -> Lấy phần đầu "en-US"
        first_part = accept_lang.split(",")[0].strip()
        # Lấy 2 ký tự đầu làm mã ngôn ngữ chính (ví dụ "en", "vi")
        lang_code = first_part.split("-")[0].lower()
        if lang_code in ("vi", "en"):
            return lang_code

    # 3. Fallback mặc định
    return "vi"
