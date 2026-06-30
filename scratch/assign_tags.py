import asyncio
from sqlalchemy import select
from app.core.database import SessionLocal
from app.modules.article.models import Article
from app.modules.tag.models import Tag
from app.modules.category.models import Category
from app.modules.auth.models import User

async def main():
    async with SessionLocal() as db:
        # Lấy 3 bài viết bất kỳ
        stmt = select(Article).limit(3)
        res = await db.execute(stmt)
        articles = res.scalars().all()
        
        if not articles:
            print("No articles found in DB.")
            return

        # Tạo hoặc lấy 2 tags mẫu
        tag1_stmt = select(Tag).where(Tag.slug == 'tuyen-sinh-2026')
        tag1_res = await db.execute(tag1_stmt)
        tag1 = tag1_res.scalar()
        if not tag1:
            tag1 = Tag(name="Tuyển sinh 2026", slug="tuyen-sinh-2026", color="#FF5733")
            db.add(tag1)
            
        tag2_stmt = select(Tag).where(Tag.slug == 'tin-tuc-noi-bat')
        tag2_res = await db.execute(tag2_stmt)
        tag2 = tag2_res.scalar()
        if not tag2:
            tag2 = Tag(name="Tin tức nổi bật", slug="tin-tuc-noi-bat", color="#007bff")
            db.add(tag2)
            
        await db.commit()
        await db.refresh(tag1)
        await db.refresh(tag2)

        # Gán tags cho các bài viết
        from sqlalchemy.orm import selectinload
        stmt_reload = select(Article).where(Article.id.in_([a.id for a in articles])).options(selectinload(Article.tags))
        res_reload = await db.execute(stmt_reload)
        articles_loaded = res_reload.scalars().all()

        # Clear tags cũ và add mới
        articles_loaded[0].tags = [tag1]
        articles_loaded[1].tags = [tag2]
        if len(articles_loaded) > 2:
            articles_loaded[2].tags = [tag1, tag2]
            
        db.add_all(articles_loaded)
        await db.commit()
        print("Successfully assigned tags to articles.")

if __name__ == "__main__":
    asyncio.run(main())
