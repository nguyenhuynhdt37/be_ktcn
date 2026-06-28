from typing import AsyncGenerator
from unittest.mock import AsyncMock
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import get_db
from app.main import app
from app.shared.redis import get_redis

# In-memory SQLite for isolated database tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

import uuid
from app.core.security import hash_password
from app.modules.auth.models import Role, User, UserRole

@pytest.fixture(autouse=True)
async def seed_test_rbac(db_session: AsyncSession):
    """
    Seeds standard Super Admin role and user in the isolated SQLite memory database.
    """
    role = Role(
        id=uuid.UUID("d1017cf7-88b3-4f9e-c616-3e4b3c75ad01"),
        name="Super Administrator",
        code="super_admin",
        description="Has full access",
    )
    db_session.add(role)

    user = User(
        id=uuid.UUID("3fa85f64-5717-4562-b3fc-2c963f66afa6"),
        username="admin",
        email="admin@university.edu.vn",
        password_hash=hash_password("adminpassword"),
        full_name="System Administrator",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    mapping = UserRole(
        user_id=user.id,
        role_id=role.id,
    )
    db_session.add(mapping)
    await db_session.commit()


@pytest.fixture(autouse=True)
async def prepare_database():
    """
    Creates all database tables in memory before each test and tears them down after.
    """
    from app.common.models.base import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Yields an isolated async session for database manipulation.
    """
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture
def mock_redis_client():
    """
    Returns a mocked Redis client.
    """
    client = AsyncMock()
    client.ping.return_value = True
    return client


@pytest.fixture
async def client(mock_redis_client) -> AsyncGenerator[AsyncClient, None]:
    """
    Yields an Async HTTP Client configured with mock DB and Redis overrides.
    """
    async def override_db():
        async with TestingSessionLocal() as session:
            yield session

    async def override_redis():
        yield mock_redis_client

    # Apply FastAPI dependency overrides
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_redis] = override_redis

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    # Clean up overrides
    app.dependency_overrides.clear()
