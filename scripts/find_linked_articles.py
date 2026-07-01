import asyncio
from sqlalchemy import text
from app.core.database import engine

async def find_linked_articles():
    async with engine.connect() as conn:
        print("🔍 Searching for articles with category_id IS NOT NULL...")
        res = await conn.execute(text("SELECT id, title, category_id, deleted_at FROM articles WHERE category_id IS NOT NULL;"))
        rows = res.fetchall()
        print(f"Total articles found: {len(rows)}")
        for r in rows[:10]:
            print(f"ID: {r[0]}, Title: {r[1]}, Category ID: {r[2]}, Deleted At: {r[3]}")
            
if __name__ == "__main__":
    asyncio.run(find_linked_articles())
