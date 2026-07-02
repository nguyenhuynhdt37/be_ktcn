import asyncio
import os
import sys

# Thêm thư mục be vào Python path để có thể import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Thiết lập biến môi trường để chạy test
os.environ["ENV"] = "development"
os.environ["AI_PROVIDER"] = "omniroute"
os.environ["AI_BASE_URL"] = "http://localhost:8090"
os.environ["AI_API_KEY"] = "sk-omniroute-secret-key"
os.environ["AI_DEFAULT_MODEL"] = "gemini-2.5-flash"

from app.core.database import SessionLocal
from app.shared.ai import get_ai_service
from app.modules.ai_hub.models import AIRequestLog
from sqlalchemy import select


async def main():
    print("Khởi chạy kiểm thử ghi nhận log AI vào PostgreSQL...")
    ai_service = get_ai_service()

    async with SessionLocal() as db:
        print("\n1. Thực hiện cuộc gọi AI (Gemini)...")
        try:
            response = await ai_service.generate_text(
                prompt="Hãy trả lời ngắn gọn: 1 + 1 bằng mấy?",
                model="gemini-2.5-flash",
                db=db,  # Truyền db session để ghi log
                username="admin_test_script"
            )
            print(f"-> Phản hồi từ AI: {response}")
        except Exception as e:
            print(f"-> Lỗi gọi AI: {e}")

        print("\n2. Thực hiện cuộc gọi AI lỗi (để kiểm tra failover log)...")
        try:
            # Gọi model sai hoặc gây lỗi
            await ai_service.generate_text(
                prompt="Test error log",
                model="model-khong-ton-tai-de-test-loi",
                db=db,
                username="admin_test_script"
            )
        except Exception as e:
            print(f"-> Ghi nhận lỗi thành công (như mong đợi): {e}")

        # Đợi một chút để session hoàn thành commit
        await db.commit()

        print("\n3. Query kiểm tra bảng ai_request_logs trong PostgreSQL...")
        query = select(AIRequestLog).order_by(AIRequestLog.created_at.desc()).limit(5)
        result = await db.execute(query)
        logs = result.scalars().all()

        print(f"Tìm thấy {len(logs)} logs gần nhất:")
        for log in logs:
            print(
                f"- [ID: {log.id}] Model: {log.model} | Status: {log.status} | Cost: ${log.cost:.6f} | Latency: {log.latency_ms}ms | User: {log.username}"
            )
            if log.error_message:
                print(f"  * Lỗi: {log.error_message[:100]}")


if __name__ == "__main__":
    asyncio.run(main())
