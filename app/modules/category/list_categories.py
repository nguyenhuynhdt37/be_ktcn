import asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.modules.category.models import Category, CategoryTranslation
from app.modules.language.models import Language

from app.core.database import get_db

async def list_cats():
    db_gen = get_db()
    db = await anext(db_gen)
    
    try:
        stmt = (
            select(Category)
            .options(
                selectinload(Category.translations).selectinload(CategoryTranslation.language)
            )
        )
        cats = (await db.execute(stmt)).scalars().all()
        
        print("DANH SÁCH CATEGORIES TRONG DB:")
        for c in cats:
            print(f"- Category ID: {c.id} | Status: {c.status}")
            for t in c.translations:
                print(f"  * Lang: {t.language.code} | Name: '{t.name}' | Slug: '{t.slug}'")
                
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(list_cats())
