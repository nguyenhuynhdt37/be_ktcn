import asyncio
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import all models and setup registries correctly
import app.main
from app.core.database import SessionLocal
from app.modules.article.models import ArticleTranslation
from app.modules.category.models import CategoryTranslation
from app.modules.department.models import DepartmentTranslation
from app.modules.program.models import ProgramTranslation
from app.core.config import settings
from sqlalchemy import select


async def migrate_urls():
    bucket = settings.MINIO_BUCKET
    # Matches: http(s)://hostname:port/bucket/ or http(s)://hostname/bucket/
    pattern = rf'https?://[^/]+/{bucket}/'
    replacement = '/api/v1/portal/media/file/'
    
    print(f"Target pattern: {pattern}")
    print(f"Replacement: {replacement}")
    
    async with SessionLocal() as db:
        print("\n🔍 Scanning article_translations...")
        stmt = select(ArticleTranslation)
        res = await db.execute(stmt)
        articles = res.scalars().all()
        updated_articles = 0
        for item in articles:
            if item.content and re.search(pattern, item.content):
                item.content = re.sub(pattern, replacement, item.content)
                db.add(item)
                updated_articles += 1
        print(f"   -> Found and updated: {updated_articles} items")
        
        print("\n🔍 Scanning category_translations...")
        stmt = select(CategoryTranslation)
        res = await db.execute(stmt)
        categories = res.scalars().all()
        updated_categories = 0
        for item in categories:
            if item.description and re.search(pattern, item.description):
                item.description = re.sub(pattern, replacement, item.description)
                db.add(item)
                updated_categories += 1
        print(f"   -> Found and updated: {updated_categories} items")
                
        print("\n🔍 Scanning department_translations...")
        stmt = select(DepartmentTranslation)
        res = await db.execute(stmt)
        depts = res.scalars().all()
        updated_depts = 0
        for item in depts:
            changed = False
            for field in ('description', 'mission', 'vision', 'history', 'research_overview'):
                val = getattr(item, field, None)
                if val and re.search(pattern, val):
                    setattr(item, field, re.sub(pattern, replacement, val))
                    changed = True
            if changed:
                db.add(item)
                updated_depts += 1
        print(f"   -> Found and updated: {updated_depts} items")
                
        print("\n🔍 Scanning program_translations...")
        stmt = select(ProgramTranslation)
        res = await db.execute(stmt)
        programs = res.scalars().all()
        updated_programs = 0
        for item in programs:
            changed = False
            for field in ('description', 'short_description'):
                val = getattr(item, field, None)
                if val and re.search(pattern, val):
                    setattr(item, field, re.sub(pattern, replacement, val))
                    changed = True
            if changed:
                db.add(item)
                updated_programs += 1
        print(f"   -> Found and updated: {updated_programs} items")
                
        total_updates = updated_articles + updated_categories + updated_depts + updated_programs
        if total_updates > 0:
            print(f"\n💾 Committing changes to database...")
            await db.commit()
            print("🎉 Migration completed successfully!")
        else:
            print("\n✅ No absolute URLs found. Database is already clean.")


if __name__ == '__main__':
    asyncio.run(migrate_urls())
