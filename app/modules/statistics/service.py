import time
import uuid
from typing import Optional, Any
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.modules.statistics.models import SystemStatistics

class StatisticsService:
    """
    Service quản lý thống kê lượt truy cập (Visits) và số người trực tuyến (Online).
    """

    async def init_statistics(self, db: AsyncSession) -> None:
        """
        Khởi tạo giá trị ban đầu cho tổng lượt truy cập là 1.703.054 nếu chưa có trong DB.
        """
        stmt = select(SystemStatistics).where(SystemStatistics.key == "total_visits")
        result = await db.execute(stmt)
        stat = result.scalar_one_or_none()
        
        if not stat:
            # Tạo mới bản ghi tổng lượt truy cập mặc định là 1.703.054
            new_stat = SystemStatistics(key="total_visits", value=1703054)
            db.add(new_stat)
            await db.commit()

    async def get_total_visits(self, redis_client: aioredis.Redis, db: AsyncSession) -> int:
        """
        Lấy tổng số lượt truy cập từ Redis cache, nếu không có sẽ đọc từ DB và lưu vào cache.
        """
        val = await redis_client.get("system:total_visits")
        if val is not None:
            return int(val)
            
        # Đọc từ DB
        stmt = select(SystemStatistics).where(SystemStatistics.key == "total_visits")
        res = await db.execute(stmt)
        stat = res.scalar_one_or_none()
        
        if stat:
            await redis_client.set("system:total_visits", str(stat.value))
            return stat.value
            
        return 0

    async def record_visit(
        self,
        guest_uuid: str,
        client_ip: str,
        redis_client: aioredis.Redis,
        db: AsyncSession
    ) -> None:
        """
        Ghi nhận sự hiện diện (online) của khách hàng và cập nhật tổng lượt truy cập (chống spam).
        """
        current_time = time.time()
        
        # 1. Cập nhật hoạt động trực tuyến vào Redis Sorted Set
        # Mỗi lượt truy cập (theo guest_uuid) được gán điểm score là epoch timestamp hiện tại.
        await redis_client.zadd("online_users", {guest_uuid: current_time})
        
        # 2. Kiểm tra xem khách hàng này (theo guest_uuid hoặc IP) đã truy cập hôm nay chưa (trong 24 giờ)
        guest_key = f"visit_today:guest:{guest_uuid}"
        ip_key = f"visit_today:ip:{client_ip}"
        
        has_visited = False
        if await redis_client.exists(guest_key):
            has_visited = True
        if not has_visited and await redis_client.exists(ip_key):
            has_visited = True
            
        if not has_visited:
            # Ghi nhận khoá đã truy cập trong 24 giờ để tránh trùng lặp
            await redis_client.set(guest_key, "1", ex=86400)
            await redis_client.set(ip_key, "1", ex=86400)
            
            # Đảm bảo Redis cache được nạp giá trị từ DB trước khi INCR
            await self.get_total_visits(redis_client, db)
            
            # Tăng tổng lượt truy cập trong Redis
            await redis_client.incr("system:total_visits")
            
            # Tăng tổng lượt truy cập trong Database
            await db.execute(
                update(SystemStatistics)
                .where(SystemStatistics.key == "total_visits")
                .values(value=SystemStatistics.value + 1)
            )
            await db.commit()

    async def get_stats(self, redis_client: aioredis.Redis, db: AsyncSession) -> dict[str, int]:
        """
        Lấy số lượng người trực tuyến (trong 5 phút qua) và tổng lượt truy cập.
        """
        current_time = time.time()
        
        # Xóa các định danh không hoạt động quá 5 phút (300 giây)
        await redis_client.zremrangebyscore("online_users", "-inf", current_time - 300)
        
        # Đếm số lượng phần tử còn lại trong Sorted Set
        online_count = await redis_client.zcard("online_users")
        
        # Đảm bảo số người online tối thiểu là 1 nếu chính bản thân khách hàng đang xem
        if online_count == 0:
            online_count = 1
            
        total_visits = await self.get_total_visits(redis_client, db)
        
        return {
            "online_count": online_count,
            "total_visits": total_visits
        }

statistics_service = StatisticsService()
