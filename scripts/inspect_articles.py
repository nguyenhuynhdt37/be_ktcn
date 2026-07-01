import asyncio
from sqlalchemy import text
from app.core.database import engine

async def inspect_articles():
    async with engine.connect() as conn:
        print("🔍 Inspecting articles...")
        res = await conn.execute(text("SELECT id, title, category_id, deleted_at FROM articles LIMIT 10;"))
        rows = res.fetchall()
        for r in rows:
            print(f"ID: {r[0]}, Title: {r[1]}, Category ID: {r[2]}, Deleted At: {r[3]}")
            
if __name__ == "__main__":
    asyncio.run(inspect_articles())
