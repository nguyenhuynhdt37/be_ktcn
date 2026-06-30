import asyncio
from sqlalchemy import update
from app.core.database import SessionLocal
from app.modules.category.models import Category

async def main():
    async with SessionLocal() as db:
        # Cập nhật slug của danh mục Nghiên cứu khoa học sang 'nckh-va-doi-ngoai'
        stmt = update(Category).where(Category.slug == 'nghien-cuu-khoa-hoc').values(slug='nckh-va-doi-ngoai')
        res = await db.execute(stmt)
        await db.commit()
        print(f"Updated {res.rowcount} category slug(s) to 'nckh-va-doi-ngoai'.")

if __name__ == "__main__":
    asyncio.run(main())
