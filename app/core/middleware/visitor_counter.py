import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
import redis.asyncio as aioredis

from app.core.config import settings
import app.shared.redis as redis_shared
from app.core.database import SessionLocal
from app.modules.statistics.service import statistics_service

class VisitorCounterMiddleware(BaseHTTPMiddleware):
    """
    Middleware tự động ghi nhận hoạt động (Online/Visits)
    và cấp phát cookie guest_uuid cho các request đến Portal.
    """
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Chỉ xử lý các API thuộc Portal và không phải API lấy thông số thống kê
        path = request.url.path
        is_portal_api = path.startswith("/api/v1/portal")
        is_stats_api = path.startswith("/api/v1/portal/statistics")

        if is_portal_api and not is_stats_api:
            # 1. Lấy guest_uuid từ Cookie
            guest_uuid = request.cookies.get("guest_uuid")
            is_new_guest = False
            
            if not guest_uuid:
                guest_uuid = str(uuid.uuid4())
                is_new_guest = True
                
            # 2. Xác định IP khách hàng
            client_ip = "unknown"
            forwarded_for = request.headers.get("X-Forwarded-For")
            if forwarded_for:
                client_ip = forwarded_for.split(",")[0].strip()
            elif request.client:
                client_ip = request.client.host
                
            # 3. Ghi nhận lượt xem và trạng thái online
            if redis_shared.redis_pool:
                redis_client = aioredis.Redis(connection_pool=redis_shared.redis_pool)
                try:
                    async with SessionLocal() as db:
                        await statistics_service.record_visit(
                            guest_uuid=guest_uuid,
                            client_ip=client_ip,
                            redis_client=redis_client,
                            db=db
                        )
                except Exception as e:
                    from loguru import logger
                    logger.exception("Error in visitor counter middleware")
                finally:
                    await redis_client.close()

            # 4. Tiếp tục xử lý request
            response = await call_next(request)
            
            # 5. Lưu cookie guest_uuid nếu là khách mới
            if is_new_guest:
                response.set_cookie(
                    key="guest_uuid",
                    value=guest_uuid,
                    httponly=True,
                    secure=settings.ENV == "production",
                    samesite="lax",
                    max_age=365 * 24 * 60 * 60,  # 1 năm
                    path="/"
                )
            return response
            
        return await call_next(request)
