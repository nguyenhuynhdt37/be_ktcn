from app.core.exceptions import AppException

class TranslationException(AppException):
    """Exception cơ sở cho các lỗi liên quan đến dịch thuật."""
    pass

class ModelNotReadyException(TranslationException):
    def __init__(self, message: str = "Mô hình dịch thuật NLLB-200 chưa sẵn sàng hoặc đang khởi động"):
        super().__init__(
            status_code=503,
            message=message,
            error_code="TRANSLATION_MODEL_NOT_READY"
        )

class InvalidInputException(TranslationException):
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            status_code=400,
            message=message,
            error_code="TRANSLATION_INVALID_INPUT",
            details=details
        )

class BatchSizeExceededException(TranslationException):
    def __init__(self, message: str = "Số lượng chuỗi cần dịch vượt quá giới hạn cấu hình"):
        super().__init__(
            status_code=400,
            message=message,
            error_code="TRANSLATION_BATCH_SIZE_EXCEEDED"
        )
