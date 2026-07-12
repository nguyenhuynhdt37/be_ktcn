"""Test script cho Admin Dashboard endpoint."""
import asyncio
import uuid
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.database import SessionLocal
from app.modules.auth.models import User
from app.modules.auth.service import hash_password


async def setup_test_user():
    async with SessionLocal() as db:
        stmt = select(User).where(User.username == "admin_api_test")
        existing = await db.execute(stmt)
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
            db.add(user)
            await db.commit()
        elif not user.is_active:
            user.is_active = True
            db.add(user)
            await db.commit()
        return "admin_api_test", "password"


async def test_dashboard():
    username, password = await setup_test_user()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Login
        login_res = await ac.post(
            "/api/v1/auth/login",
            json={"username": username, "password": password},
        )
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Test dashboard
        print("\n🔍 Testing GET /api/v1/admin/dashboard ...")
        res = await ac.get("/api/v1/admin/dashboard", headers=headers)
        print(f"   Status: {res.status_code}")

        if res.status_code != 200:
            print(f"   ❌ FAILED: {res.text}")
            return False

        data = res.json()

        # Validate structure
        required_keys = [
            "visitors", "articles", "users", "consultations",
            "content", "logins", "top_articles", "recent_activities",
        ]
        for key in required_keys:
            assert key in data, f"Missing key: {key}"
            print(f"   ✅ {key}: present")

        # Validate visitors
        v = data["visitors"]
        assert "online_count" in v and "total_visits" in v
        print(f"\n📊 Visitors: online={v['online_count']}, total_visits={v['total_visits']}")

        # Validate articles
        a = data["articles"]
        print(f"📝 Articles: total={a['total']}, published={a['published']}, draft={a['draft']}, scheduled={a['scheduled']}, archived={a['archived']}, trash={a['trash']}, views={a['total_views']}")

        # Validate users
        u = data["users"]
        print(f"👤 Users: total={u['total']}, active={u['active']}, locked={u['locked']}, deleted={u['deleted']}")

        # Validate consultations
        c = data["consultations"]
        print(f"📋 Consultations: total={c['total']}, new={c['new']}, contacted={c['contacted']}, consulting={c['consulting']}, completed={c['completed']}")

        # Validate content
        ct = data["content"]
        storage_mb = ct["media_storage_bytes"] / (1024 * 1024) if ct["media_storage_bytes"] > 0 else 0
        print(f"📁 Content: departments={ct['departments']}, categories={ct['categories']}, banners={ct['banners']}, media={ct['media_count']} files ({storage_mb:.1f} MB)")

        # Validate logins
        l = data["logins"]
        print(f"🔐 Logins: today={l['today']}, 7days={l['last_7_days']}, failed_today={l['failed_today']}")

        # Validate top articles
        ta = data["top_articles"]
        print(f"\n🏆 Top {len(ta)} articles:")
        for i, art in enumerate(ta, 1):
            print(f"   {i}. {art['title'][:60]} (views: {art['view_count']})")

        # Validate recent activities
        ra = data["recent_activities"]
        print(f"\n📜 Recent {len(ra)} activities:")
        for act in ra[:5]:
            print(f"   - {act['actor_username']} → {act['action']} ({act['target_type']})")

        print("\n✅ Dashboard API test PASSED!")
        return True


if __name__ == "__main__":
    result = asyncio.run(test_dashboard())
    sys.exit(0 if result else 1)
