import asyncio
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app.main
from app.core.database import SessionLocal
from app.modules.article.models import ArticleTranslation


async def verify():
    async with SessionLocal() as db:
        res = await db.execute(select_stmt := select(ArticleTranslation))
        items = res.scalars().all()
        
        relative_count = sum(1 for x in items if x.content and '/api/v1/portal/media/file/' in x.content)
        localhost_count = sum(1 for x in items if x.content and 'localhost:9000' in x.content)
        total_with_images = sum(1 for x in items if x.content and '<img' in x.content)
        
        print(f"Total translation rows: {len(items)}")
        print(f"Rows containing images (<img): {total_with_images}")
        print(f"Rows containing relative path (/api/v1/portal/media/file/): {relative_count}")
        print(f"Rows containing localhost:9000: {localhost_count}")
        
        for x in items:
            if x.content and '/api/v1/portal/media/file/' in x.content:
                print("\n--- SAMPLE ARTICLE WITH RELATIVE IMAGE PATHS ---")
                print("Title:", x.title)
                imgs = re.findall(r'<img [^>]*src=\"([^\"]+)\"', x.content)
                print("Image URLs found in content:", imgs)
                break

from sqlalchemy import select
if __name__ == '__main__':
    asyncio.run(verify())
