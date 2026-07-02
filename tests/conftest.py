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
            
    yield "admin_api_test", "password"

    # Teardown: Xóa cứng sạch sẽ
    async with SessionLocal() as db_session:
        existing = await db_session.execute(
            select(User).where(User.username == "admin_api_test")
        )
        user = existing.scalar_one_or_none()
        if user:
            from sqlalchemy import delete
            from app.modules.auth.models import LoginHistory, RefreshToken
            from app.modules.audit.models import AuditLog
            
            await db_session.execute(delete(LoginHistory).where(LoginHistory.user_id == user.id))
            await db_session.execute(delete(RefreshToken).where(RefreshToken.user_id == user.id))
            await db_session.execute(delete(AuditLog).where(AuditLog.actor_id == user.id))
            await db_session.delete(user)
            await db_session.commit()


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


from unittest.mock import patch

@pytest.fixture(autouse=True)
def mock_ai_service():
    def mock_translate_text(text: str) -> str:
        mapping = {
            "Khoa Khoa học Máy tính": "Department of Computer Science",
            "Tuyển sinh năm 2026": "Enrollment in 2026",
            "Tuyển sinh": "Admissions",
            "Nghiên cứu khoa học": "Scientific research",
            "giảng viên": "lecturer",
            "vào đây": "here",
            "Họ và Tên": "Full Name",
            "Chức vụ": "Position",
            "Nguyễn Văn A": "Nguyen Van A",
            "Trưởng bộ môn": "Head of Department",
            "Xin chào": "Hello",
            "Thông báo tuyển sinh năm 2026": "Enrollment announcement for 2026",
            "Thông báo": "Announcement",
        }
        result = text
        for k, v in mapping.items():
            result = result.replace(k, v)
        return result

    with patch("app.shared.ai.service.AIService.generate_text") as mock_gen:
        async def mock_generate(prompt, system_instruction=None, **kwargs):
            import json
            # Trích xuất nội dung cần dịch từ prompt
            content = prompt.split(":\n")[-1].strip()
            
            if "JSON" in (system_instruction or ""):
                try:
                    texts = json.loads(content)
                    return json.dumps([mock_translate_text(t) for t in texts], ensure_ascii=False)
                except:
                    return json.dumps(["Mocked translation"])
            
            return mock_translate_text(content)
            
        mock_gen.side_effect = mock_generate
        yield mock_gen

