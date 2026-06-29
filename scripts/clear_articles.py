import asyncio
import sys
import os
from loguru import logger
from sqlalchemy import delete

# Thêm root dự án vào path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.modules.article.models import Article

async def clear_all_articles():
    async with SessionLocal() as db:
        logger.info("🗑️ Đang tiến hành xóa cứng toàn bộ bài viết (articles) khỏi database...")
        
        # Xóa cứng toàn bộ bản ghi trong bảng articles
        # Do khóa ngoại tại article_tags cấu hình ondelete="CASCADE" nên sẽ tự động dọn sạch article_tags
        stmt = delete(Article)
        result = await db.execute(stmt)
        await db.commit()
        
        logger.info(f"✅ Đã dọn dẹp sạch sẽ: Xóa cứng thành công {result.rowcount} bài viết.")

if __name__ == "__main__":
    asyncio.run(clear_all_articles())
