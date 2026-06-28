import asyncio
from datetime import datetime, timedelta
from loguru import logger
from app.core.database import SessionLocal
from app.modules.ai.service import ai_service


async def start_daily_ai_sync_task() -> None:
    """
    Task chạy nền lập lịch tự động: mỗi 00:00 (nửa đêm) hàng ngày sẽ tự động quét,
    kiểm tra khả dụng các model AI và đồng bộ lại bảng giá mà không cần Admin can thiệp.
    """
    logger.info("AI daily synchronization scheduler task started successfully.")
    
    while True:
        # 1. Tính toán thời gian tới 00:00 ngày tiếp theo (local time)
        now = datetime.now()
        tomorrow_midnight = datetime(now.year, now.month, now.day) + timedelta(days=1)
        seconds_to_wait = (tomorrow_midnight - now).total_seconds()
        
        logger.info(f"AI Sync scheduler: Sleeping for {seconds_to_wait:.1f} seconds until next midnight ({tomorrow_midnight})")
        
        # 2. Ngủ cho tới nửa đêm
        await asyncio.sleep(seconds_to_wait)
        
        # 3. Thức dậy và chạy đồng bộ
        logger.info("AI Sync scheduler: Midnight reached! Executing daily sync...")
        try:
            async with SessionLocal() as db:
                await ai_service.sync_active_provider_models(db)
                await db.commit()
            logger.info("AI Sync scheduler: Daily sync completed successfully.")
        except Exception as e:
            logger.error(f"AI Sync scheduler: Daily sync failed with error: {str(e)}")
