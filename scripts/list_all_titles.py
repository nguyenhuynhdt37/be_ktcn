import asyncio
from sqlalchemy import text
from app.core.database import engine

async def list_titles():
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT id, title FROM articles;"))
        rows = res.fetchall()
        print(f"Total articles: {len(rows)}")
        for idx, r in enumerate(rows):
            print(f"{idx+1}. ID: {r[0]} | Title: {r[1]}")

if __name__ == "__main__":
    asyncio.run(list_titles())
