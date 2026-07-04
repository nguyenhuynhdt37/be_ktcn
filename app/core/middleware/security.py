from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to inject critical security headers into every HTTP response.
    Protects against clickjacking, MIME-sniffing, and cross-site scripting (XSS).
    """
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)
        
        # Prevent Clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent MIME-Sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Enable XSS protection in older browsers
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Control Referrer information disclosure
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Force HTTPS in production (HSTS)
        if settings.ENV == "production" or request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains; preload"
            )
            
        return response


class RequestSizeLimiterMiddleware(BaseHTTPMiddleware):
    """
    Middleware to limit the maximum allowed content size of HTTP requests.
    Prevents Denial of Service (DoS) attacks via massive payloads.
    """
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Check Content-Length header first
        content_length = request.headers.get("content-length")
        
        if content_length:
            try:
                size = int(content_length)
                if size > settings.MAX_CONTENT_LENGTH:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": {
                                "code": "PAYLOAD_TOO_LARGE",
                                "message": f"Payload size exceeds the limit of {settings.MAX_CONTENT_LENGTH // (1024 * 1024)}MB."
                            }
                        }
                    )
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": {
                            "code": "BAD_REQUEST",
                            "message": "Invalid Content-Length header."
                        }
                    }
                )
                
        return await call_next(request)
