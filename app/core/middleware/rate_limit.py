import time
from typing import Any
import jwt
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse
import redis.asyncio as aioredis
from loguru import logger

from app.core.config import settings
from app.core.security import decode_access_token
from app.shared import redis

# Redis Lua Script for Sliding Window Rate Limiting (Atomic Operation)
SLIDING_WINDOW_SCRIPT = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local clear_before = now - window

redis.call('ZREMRANGEBYSCORE', key, 0, clear_before)
local count = redis.call('ZCARD', key)

if count < limit then
    redis.call('ZADD', key, now, now)
    redis.call('EXPIRE', key, math.ceil(window / 1000))
    return 1
else
    return 0
end
"""


def parse_rate_limit_string(limit_str: str) -> tuple[int, int]:
    """
    Parses limit strings like '100/minute', '5/second' into (limit_count, window_ms).
    """
    try:
        parts = limit_str.split("/")
        limit = int(parts[0])
        unit = parts[1].strip().lower()
        if unit == "second":
            return limit, 1000
        elif unit == "minute":
            return limit, 60000
        elif unit == "hour":
            return limit, 3600000
        elif unit == "day":
            return limit, 86400000
        return limit, 60000
    except Exception as e:
        logger.error(f"Error parsing rate limit string '{limit_str}': {e}. Using default 100/minute.")
        return 100, 60000


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Redis-based Sliding Window Rate Limiting Middleware.
    Distinguishes limits by endpoint types (Auth, AI/Translation, Global)
    and uses User ID (if authenticated) or Client IP.
    """
    def __init__(self, app: Any):
        super().__init__(app)
        self.lua_script = None

    def _get_limit_for_path(self, path: str) -> tuple[int, int, str]:
        """
        Returns (limit, window_ms, limit_category) based on request path.
        """
        # Auth endpoints
        if "/auth/login" in path or "/auth/register" in path:
            limit, window = parse_rate_limit_string(settings.RATE_LIMIT_AUTH)
            return limit, window, "auth"
            
        # AI & Translation endpoints (expensive)
        if "/translation" in path or "/ai-hub" in path or "/seo/" in path:
            limit, window = parse_rate_limit_string(settings.RATE_LIMIT_AI)
            return limit, window, "ai"
            
        # Default global endpoints
        limit, window = parse_rate_limit_string(settings.RATE_LIMIT_GLOBAL)
        return limit, window, "global"

    def _extract_client_ip(self, request: Request) -> str:
        """
        Safely extracts client IP, honoring trusted proxy headers.
        """
        # Trust Cloudflare proxy header first
        cf_ip = request.headers.get("cf-connecting-ip")
        if cf_ip:
            return cf_ip
            
        # Trust X-Real-IP
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
            
        # Parse X-Forwarded-For
        xff = request.headers.get("x-forwarded-for")
        if xff:
            return xff.split(",")[0].strip()
            
        return request.client.host if request.client else "unknown"

    def _get_user_id_from_token(self, request: Request) -> str | None:
        """
        Extracts User ID (sub) from Authorization JWT token if valid.
        """
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
            
        token = auth_header.split(" ")[1]
        try:
            payload = decode_access_token(token)
            return str(payload.get("sub"))
        except (jwt.PyJWTError, Exception):
            # If token is invalid/expired, we fall back to IP-based rate limiting
            return None

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip rate limiting for docs, redoc, health checks, or if Redis is not initialized
        path = request.url.path
        if (
            path == "/health" 
            or path.startswith("/docs") 
            or path.startswith("/redoc") 
            or path == "/openapi.json"
            or redis.redis_pool is None
        ):
            return await call_next(request)

        # 1. Determine rate limit values
        limit, window_ms, category = self._get_limit_for_path(path)

        # 2. Determine Identifier (User ID if logged in, otherwise Client IP)
        user_id = self._get_user_id_from_token(request)
        if user_id:
            identifier_key = f"ratelimit:{category}:user:{user_id}"
        else:
            client_ip = self._extract_client_ip(request)
            identifier_key = f"ratelimit:{category}:ip:{client_ip}"

        # 3. Apply Sliding Window Limit using Redis Script
        logger.info(f"RateLimit Check | Path: {path} | Category: {category} | Limit: {limit} | Key: {identifier_key} | User ID: {user_id}")
        try:
            # Create redis client using global pool
            redis_client = aioredis.Redis(connection_pool=redis.redis_pool)
            
            # Register lua script if not cached
            if not self.lua_script:
                self.lua_script = redis_client.register_script(SLIDING_WINDOW_SCRIPT)

            now_ms = int(time.time() * 1000)
            
            # Execute Script
            allowed = await self.lua_script(
                keys=[identifier_key],
                args=[now_ms, window_ms, limit]
            )

            # Close client back to pool
            await redis_client.close()

            if not allowed:
                logger.warning(f"Rate limit exceeded for key {identifier_key} on path {path}")
                
                # Estimate retry after time (roughly window size in seconds)
                retry_after_seconds = math_ceil_seconds = int(window_ms / 1000)
                
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": {
                            "code": "TOO_MANY_REQUESTS",
                            "message": "Too many requests. Please try again later.",
                            "retry_after_seconds": retry_after_seconds
                        }
                    },
                    headers={"Retry-After": str(retry_after_seconds)}
                )

        except Exception as e:
            # Fail-safe: If Redis fails, log the error and allow request to pass through
            logger.error(f"Redis rate limiting failed: {e}. Allow request to pass.")
            
        return await call_next(request)
