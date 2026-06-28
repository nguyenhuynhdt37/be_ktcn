from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppException(Exception):
    """
    Base class for all application-specific exceptions.
    """

    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.details = details or {}


class BadRequestException(AppException):
    def __init__(
        self,
        message: str = "Yêu cầu không hợp lệ",
        error_code: str = "BAD_REQUEST",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(400, error_code, message, details)


class UnauthorizedException(AppException):
    def __init__(
        self,
        message: str = "Không có quyền truy cập",
        error_code: str = "UNAUTHORIZED",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(401, error_code, message, details)


class ForbiddenException(AppException):
    def __init__(
        self,
        message: str = "Không được phép truy cập",
        error_code: str = "FORBIDDEN",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(403, error_code, message, details)


class NotFoundException(AppException):
    def __init__(
        self,
        message: str = "Không tìm thấy tài nguyên",
        error_code: str = "NOT_FOUND",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(404, error_code, message, details)


class ConflictException(AppException):
    def __init__(
        self,
        message: str = "Xung đột tài nguyên",
        error_code: str = "CONFLICT",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(409, error_code, message, details)


class InternalServerException(AppException):
    def __init__(
        self,
        message: str = "Lỗi hệ thống xảy ra",
        error_code: str = "INTERNAL_SERVER_ERROR",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(500, error_code, message, details)


class TooManyRequestsException(AppException):
    def __init__(
        self,
        message: str = "Quá nhiều yêu cầu, vui lòng thử lại sau",
        error_code: str = "TOO_MANY_REQUESTS",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(429, error_code, message, details)


# Handlers
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    Global handler for custom AppExceptions.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            },
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Global handler for FastAPI request/Pydantic validation errors.
    """
    details = {}
    for error in exc.errors():
        # Parse path key (e.g. body -> username)
        loc = ".".join(str(x) for x in error.get("loc", []))
        details[loc] = error.get("msg")

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Dữ liệu đầu vào không hợp lệ",
                "details": details,
            },
        },
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """
    Global handler for standard Starlette/FastAPI HTTPExceptions (e.g. 404, 405).
    """
    error_code = "HTTP_ERROR"
    if exc.status_code == 404:
        error_code = "NOT_FOUND"
    elif exc.status_code == 401:
        error_code = "UNAUTHORIZED"
    elif exc.status_code == 403:
        error_code = "FORBIDDEN"
    elif exc.status_code == 405:
        error_code = "METHOD_NOT_ALLOWED"

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": error_code,
                "message": exc.detail,
                "details": {},
            },
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all exception handler for unhandled application errors.
    Logs tracebacks and returns a generic envelope.
    """
    logger.exception(f"Unhandled error occurred: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Có lỗi hệ thống xảy ra. Vui lòng liên hệ quản trị viên.",
                "details": {},
            },
        },
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Registers the exception handlers on the FastAPI application instance.
    """
    app.add_exception_handler(AppException, app_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, general_exception_handler)
