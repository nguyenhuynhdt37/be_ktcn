import asyncio
from sqlalchemy import select, delete
from app.core.database import SessionLocal
# Import models to register them in SQLAlchemy's metadata registry
from app.modules.auth.models import User
from app.modules.category.models import Category
from app.modules.article.models import Article
from app.modules.tag.models import Tag

async def main():
    async with SessionLocal() as db:
        res = await db.execute(select(Article))
        articles = res.scalars().all()
        print(f"Total articles before: {len(articles)}")
        
        stmt = delete(Article)
        res = await db.execute(stmt)
        await db.commit()
        
        # Verify
        res_after = await db.execute(select(Article))
        articles_after = res_after.scalars().all()
        print(f"Total articles after: {len(articles_after)}")
        print(f"Successfully deleted {res.rowcount} articles.")

if __name__ == "__main__":
    asyncio.run(main())
