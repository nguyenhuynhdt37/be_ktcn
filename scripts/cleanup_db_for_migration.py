import asyncio
from sqlalchemy import text
from app.core.database import engine

async def cleanup():
    async with engine.connect() as conn:
        print("🧹 Đang dọn dẹp Database dev...")
        # 1. Drop bảng category_translations
        await conn.execute(text("DROP TABLE IF EXISTS category_translations CASCADE;"))
        print("  - Đã DROP bảng category_translations (nếu có)")
        
        # 2. Set alembic version về c289ccee0b64
        await conn.execute(text("UPDATE alembic_version SET version_num = 'c289ccee0b64';"))
        print("  - Đã đặt alembic_version về 'c289ccee0b64'")
        
        await conn.commit()
    print("✅ Dọn dẹp Database hoàn tất!")

if __name__ == "__main__":
    asyncio.run(cleanup())
