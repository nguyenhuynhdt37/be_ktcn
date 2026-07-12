import asyncio
import sys
import os
import json
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app.main
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import SessionLocal
from app.modules.article.models import ArticleTranslation
from sqlalchemy import select


async def verify_api():
    # 1. Get a slug from the database that we know has images
    async with SessionLocal() as db:
        res = await db.execute(select(ArticleTranslation))
        items = res.scalars().all()
        target_slug = None
        for item in items:
            if item.content and '/api/v1/portal/media/file/' in item.content:
                target_slug = item.slug
                print(f"Target article slug: {target_slug}")
                break
        
        if not target_slug:
            print("No articles with images found in DB!")
            return False

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        print(f"Fetching /api/v1/portal/articles/{target_slug} ...")
        res = await ac.get(f"/api/v1/portal/articles/{target_slug}")
        assert res.status_code == 200, f"API failed: {res.text}"
        
        item = res.json()
        content = item.get("content", "")
        
        print("\nArticle Title:", item.get("title"))
        
        found_resolved = "http://localhost:9000/university-media/" in content
        found_relative = "/api/v1/portal/media/file/" in content
        
        print(f"Absolute URLs resolved: {found_resolved}")
        print(f"Relative URLs left unresolved: {found_relative}")
        
        urls = re.findall(r'src="([^"]+)"', content)
        print("URLs in serialized HTML content:", urls[:5])
        
        assert not found_relative, "Error: Relative URLs found in serialized API response!"
        assert found_resolved, "Error: No absolute resolved URLs found in API response!"
        print("\n✅ Verification PASSED: Dynamic API URL serialization is working perfectly!")
        return True


if __name__ == '__main__':
    result = asyncio.run(verify_api())
    sys.exit(0 if result else 1)
