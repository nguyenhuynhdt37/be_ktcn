import asyncio
import uuid
import pytest
from collections.abc import AsyncGenerator
import httpx
from sqlalchemy import select

from app.main import app
from app.core.database import SessionLocal
from app.modules.auth.models import User
from app.core.security import hash_password


@pytest.fixture(scope="session")
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[SessionLocal, None]:
    async with SessionLocal() as session:
        yield session


@pytest.fixture(scope="function")
async def admin_credentials() -> tuple[str, str]:
    async with SessionLocal() as db_session:
        existing = await db_session.execute(
            select(User).where(User.username == "admin_api_test")
        )
        user = existing.scalar_one_or_none()
        if not user:
            user = User(
                id=uuid.uuid4(),
                username="admin_api_test",
                email="admin_api@test.com",
                password_hash=hash_password("password"),
                full_name="Admin API Test",
                is_active=True,
            )
            db_session.add(user)
            await db_session.commit()
    return "admin_api_test", "password"


@pytest.fixture(scope="function")
async def client() -> AsyncGenerator[httpx.AsyncClient, None]:
    async with httpx.AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="function")
async def admin_headers(client, admin_credentials) -> dict[str, str]:
    username, password = admin_credentials
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
