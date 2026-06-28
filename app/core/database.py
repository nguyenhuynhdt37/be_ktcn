from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# Configure async engine with production-ready connection pooling
engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    echo=settings.DEBUG,
    pool_pre_ping=True,  # Check connection health before using it
    pool_size=20,  # Number of permanent connections
    max_overflow=10,  # Temporary overflow connections
)

# Async session factory
SessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection provider for SQLAlchemy database sessions.
    Automatically handles session lifecycle and disposal.
    """
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
