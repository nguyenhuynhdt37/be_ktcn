import asyncio
import uuid
import sys
import os
from loguru import logger
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine
from app.modules.article.models import Article, ArticleStatus
from app.modules.category.models import Category
from app.modules.auth.models import User
from app.modules.article.event_dispatcher import ArticlePublishedEvent, publish_event_dispatcher
from app.modules.knowledge.models import KnowledgeChunk, KnowledgeEntity, KnowledgeRelationship
from app.modules.ai.models import AISetting

async def run_e2e_test():
    logger.info("Starting E2E AI Flow Test...")
    
    async with SessionLocal() as db:
        pass

            
        # Ensure we have active AI Settings
        setting_heavy = await db.execute(select(AISetting).where(AISetting.setting_type == "heavy_lifter"))
        if not setting_heavy.scalars().first():
            db.add(AISetting(provider="mock", model="mock", setting_type="heavy_lifter", is_active=True))
        
        setting_embed = await db.execute(select(AISetting).where(AISetting.setting_type == "embedding"))
        if not setting_embed.scalars().first():
            db.add(AISetting(provider="mock", model="mock", setting_type="embedding", is_active=True))
            
        await db.commit()

        import random
        rnd = random.randint(1000, 9999)
        # 1. Create User
        user_id = uuid.uuid4()
        user = User(id=user_id, username=f"test_e2e_{rnd}", email=f"test{rnd}@e2e.com", password_hash="xxx", full_name="Test User", is_active=True)
        db.add(user)

        # 2. Create Category
        cat_id = uuid.uuid4()
        cat = Category(id=cat_id, name=f"Test Cat {rnd}", slug=f"test-cat-{rnd}", status="ACTIVE")
        db.add(cat)
        await db.flush()

        # 3. Create Article
        article_id = uuid.uuid4()
        article = Article(
            id=article_id,
            title=f"Sự kiện ra mắt AI mới của Google và OpenAI {rnd}",
            slug=f"su-kien-ra-mat-ai-moi-cua-google-{rnd}",
            content="Vào hôm nay, Google đã ra mắt phiên bản Gemini Pro mới. Trong khi đó, OpenAI cũng không kém cạnh với GPT-4 Turbo. Hai công ty công nghệ hàng đầu này đang cạnh tranh khốc liệt trong mảng Trí tuệ nhân tạo.",
            short_description="Cuộc đua AI giữa Google và OpenAI.",
            status=ArticleStatus.DRAFT,
            category_id=cat_id,
            author_id=user_id
        )
        db.add(article)
        await db.commit()
        
        logger.info(f"Created Article {article_id}")

        # 4. Trigger Publish Event
        event = ArticlePublishedEvent(article_id=article_id, slug=article.slug)
        await publish_event_dispatcher.dispatch(event)
        
        logger.info(f"Published event dispatched. Waiting for background tasks to finish (30 seconds)...")
        await asyncio.sleep(30) # Give workers time to run
        
        # 5. Assertions
        chunks_res = await db.execute(select(KnowledgeChunk).where(KnowledgeChunk.source_id == article_id))
        chunks = chunks_res.scalars().all()
        logger.info(f"Found {len(chunks)} chunks.")
        
        if len(chunks) == 0:
            logger.error("TEST FAILED: No KnowledgeChunks created.")
            return

        entities_res = await db.execute(select(KnowledgeEntity))
        entities = entities_res.scalars().all()
        logger.info(f"Found {len(entities)} KnowledgeEntities.")
        for e in entities:
            logger.info(f" - Entity: {e.name} ({e.entity_type})")
            
        rel_res = await db.execute(select(KnowledgeRelationship))
        rels = rel_res.scalars().all()
        logger.info(f"Found {len(rels)} KnowledgeRelationships.")
        
        logger.info("E2E Test Completed Successfully!")

if __name__ == "__main__":
    asyncio.run(run_e2e_test())
