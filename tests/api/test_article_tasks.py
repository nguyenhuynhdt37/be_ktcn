import pytest
from datetime import datetime, timezone, timedelta
from app.modules.article.tasks import unpublish_expired_articles
from app.modules.article.models import Article, ArticleStatus
from app.core.database import SessionLocal
from uuid import uuid4

@pytest.mark.asyncio
async def test_unpublish_expired_articles(db_session):
    now = datetime.now(timezone.utc)
    
    # 1. Create a published article that is expired
    expired_article = Article(
        id=uuid4(),
        title="Expired Article",
        slug="expired-article",
        status=ArticleStatus.PUBLISHED,
        author_id=uuid4(),
        version=1,
        word_count=100,
        reading_time=1,
        scheduled_unpublish_at=now - timedelta(days=1)
    )
    db_session.add(expired_article)
    
    # 2. Create a published article that is NOT expired
    valid_article = Article(
        id=uuid4(),
        title="Valid Article",
        slug="valid-article",
        status=ArticleStatus.PUBLISHED,
        author_id=uuid4(),
        version=1,
        word_count=100,
        reading_time=1,
        scheduled_unpublish_at=now + timedelta(days=1)
    )
    db_session.add(valid_article)
    await db_session.commit()
    
    # Check initial statuses
    assert expired_article.status == ArticleStatus.PUBLISHED
    assert valid_article.status == ArticleStatus.PUBLISHED
    
    # Run task
    await unpublish_expired_articles(db_session)
    
    # Refetch from DB
    await db_session.refresh(expired_article)
    await db_session.refresh(valid_article)
    
    # Expired should be DRAFT or whatever unpublish returns (usually DRAFT)
    assert expired_article.status == ArticleStatus.DRAFT
    # Valid should remain PUBLISHED
    assert valid_article.status == ArticleStatus.PUBLISHED
