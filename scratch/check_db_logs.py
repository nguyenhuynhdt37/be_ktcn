import asyncio
import os
import sys

# Thêm thư mục be vào Python path để có thể import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.modules.ai_hub.models import AIRequestLog
from sqlalchemy import select


async def main():
    print("Truy xuất 5 logs gần nhất từ database PostgreSQL...")
    async with SessionLocal() as db:
        query = select(AIRequestLog).order_by(AIRequestLog.created_at.desc()).limit(5)
        result = await db.execute(query)
        logs = result.scalars().all()

        if not logs:
            print("Không tìm thấy log nào trong DB!")
            return

        for idx, log in enumerate(logs):
            print("=" * 60)
            print(f"LOG #{idx+1} [ID: {log.id}]")
            print(f"Thời gian: {log.created_at}")
            print(f"Model: {log.model} | Status: {log.status} | Latency: {log.latency_ms}ms")
            print(f"User: {log.username} | Cost: ${log.cost:.6f}")
            print("-" * 30)
            print(f"PROMPT gửi đi:\n{log.prompt}")
            print("-" * 30)
            if log.status == "SUCCESS":
                print(f"RESPONSE nhận về:\n{log.response}")
            else:
                print(f"ERROR MESSAGE:\n{log.error_message}")
            print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
