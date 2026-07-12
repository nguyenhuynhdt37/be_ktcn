import asyncio
import sys
import os
import io

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app.main
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import SessionLocal
from sqlalchemy import select
from app.modules.auth.models import User
from app.modules.auth.service import hash_password
import uuid


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


async def test_portal_media():
    username, password = await setup_test_user()
    transport = ASGITransport(app=app)
    
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Login
        login_res = await ac.post(
            "/api/v1/auth/login",
            json={"username": username, "password": password},
        )
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 1. Upload a file
        print("Uploading file via Admin API...")
        file_data = b"Hello Portal Media Test Content - 123456"
        files = {"file": ("test_portal.txt", file_data, "text/plain")}
        
        upload_res = await ac.post(
            "/api/v1/admin/media/upload",
            files=files,
            headers=headers
        )
        assert upload_res.status_code == 200, f"Upload failed: {upload_res.text}"
        uploaded_item = upload_res.json()
        object_key = uploaded_item["object_key"]
        print(f"Uploaded successfully. Object Key: {object_key}")
        
        # 2. Get URL
        url_res = await ac.get(
            f"/api/v1/admin/media/{uploaded_item['id']}/url",
            headers=headers
        )
        assert url_res.status_code == 200
        url_data = url_res.json()
        print(f"Generated URL from admin endpoint: {url_data['url']}")
        
        # Expected relative path
        expected_url = f"/api/v1/portal/media/file/{object_key}"
        assert url_data["url"] == expected_url, f"Expected {expected_url}, got {url_data['url']}"
        print("   -> URL format matches expected relative path!")
        
        # 3. Retrieve file from public Portal endpoint (NO headers/auth)
        print("Downloading file via Public Portal endpoint (without Authentication)...")
        download_res = await ac.get(url_data["url"])
        
        print(f"   Status code: {download_res.status_code}")
        assert download_res.status_code == 200
        
        print(f"   Response Content: '{download_res.text}'")
        assert download_res.content == file_data
        print("   -> Downloaded content matches uploaded content exactly!")
        
        # Cleanup file from DB and S3 (Optional, but let's test deleting)
        print("Cleaning up file...")
        del_res = await ac.delete(
            f"/api/v1/admin/media/{uploaded_item['id']}",
            headers=headers
        )
        assert del_res.status_code == 200
        print("Cleanup successful.")
        
        print("\n🎉 Portal Media Flow Test Passed successfully!")
        return True


if __name__ == '__main__':
    result = asyncio.run(test_portal_media())
    sys.exit(0 if result else 1)
