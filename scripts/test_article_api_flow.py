import asyncio
import uuid
import sys
import os
from loguru import logger
import httpx

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.core.database import SessionLocal
from app.modules.auth.models import User
from app.core.security import hash_password

async def setup_test_user():
    from sqlalchemy import select
    async with SessionLocal() as db:
        from app.modules.auth.models import Role, UserRole
        role = await db.execute(select(Role).where(Role.code == "super_admin"))
        sa_role = role.scalar_one_or_none()
        
        existing = await db.execute(select(User).where(User.username == "admin_api_test"))
        user = existing.scalar_one_or_none()
        if not user:
            user_id = uuid.uuid4()
            user = User(
                id=user_id, 
                username="admin_api_test", 
                email="admin_api@test.com", 
                password_hash=hash_password("password"), 
                full_name="Admin API Test", 
                is_active=True
            )
            db.add(user)
            await db.flush() # get id
            if sa_role:
                db.add(UserRole(user_id=user_id, role_id=sa_role.id))
            await db.commit()
        else:
            # ensure role
            if sa_role:
                existing_role = await db.execute(select(UserRole).where(UserRole.user_id == user.id, UserRole.role_id == sa_role.id))
                if not existing_role.scalar_one_or_none():
                    db.add(UserRole(user_id=user.id, role_id=sa_role.id))
                    await db.commit()
                    
        return "admin_api_test", "password"

async def test_api_flow():
    logger.info("Setting up test user...")
    email, password = await setup_test_user()

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test/api/v1") as client:
        logger.info("1. Login as Admin")
        login_data = {"username": email, "password": password}
        resp = await client.post("/auth/login", json=login_data)
        if resp.status_code != 200:
            logger.error(f"Login failed: {resp.text}")
            return
            
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        logger.info("-> Login successful, Token acquired.")
        
        logger.info("2. Create Category")
        cat_resp = await client.post("/categories", json={
            "name": "E2E API Test Cat",
            "slug": f"e2e-api-cat-{uuid.uuid4().hex[:6]}",
            "description": "Category for E2E testing"
        }, headers=headers)
        
        if cat_resp.status_code == 201:
            category_id = cat_resp.json()["id"]
        elif cat_resp.status_code == 400: # Exists
            cats = await client.get("/categories", headers=headers)
            category_id = cats.json()["items"][0]["id"]
        else:
            logger.error(f"Category creation failed: {cat_resp.text}")
            return
            
        logger.info(f"-> Category ID: {category_id}")
            
        logger.info("3. Create Article Draft (A -> Z Flow)")
        draft_resp = await client.post("/articles/drafts", json={
            "title": "Quy trình tạo bài viết từ A-Z với API",
            "content": "Nội dung bài viết thử nghiệm luồng A-Z qua FastAPI. AI sẽ sinh SEO và Audio.",
            "short_description": "Test luồng A-Z",
            "category_id": category_id
        }, headers=headers)
        
        if draft_resp.status_code != 201:
            logger.error(f"Create draft failed: {draft_resp.text}")
            return
            
        article = draft_resp.json()
        article_id = article["id"]
        logger.info(f"-> Created Article Draft ID: {article_id}")
        logger.info(f"-> Initial Status: {article['status']}")
        
        logger.info("4. Generate AI SEO")
        # Ensure setting exists for AI
        from app.modules.ai.models import AISetting
        from sqlalchemy import select
        async with SessionLocal() as db:
            setting_text = await db.execute(select(AISetting).where(AISetting.setting_type == "text"))
            if not setting_text.scalars().first():
                db.add(AISetting(provider="mock", model="mock", setting_type="text", is_active=True))
                await db.commit()

        # Update draft with tts_voices
        logger.info("-> Updating Draft with Multiple TTS Voices")
        update_resp = await client.patch(f"/articles/drafts/{article_id}", json={
            "tts_voices": ["banmai", "minhquang"],
            "version": article["version"]
        }, headers=headers)
        if update_resp.status_code == 200:
            logger.info(f"   Updated tts_voices: {update_resp.json().get('tts_voices')}")
        else:
            logger.error(f"   Failed to update draft: {update_resp.text}")
            
        logger.info("3.5. Test TTS API Key & Preview")
        test_conn = await client.post("/ai/test-connection", json={
            "provider": "fpt",
            "model": "banmai",
            "setting_type": "text"
        }, headers=headers)
        if test_conn.status_code == 200:
            logger.info("-> FPT Test Connection OK (Voices populated)")
        
        preview_resp = await client.post("/ai/tts/preview", json={
            "voice_code": "banmai",
            "text": "Tôi là trợ lý tạo giọng đọc của Trường Kỹ Thuật Công Nghệ - Đại Học Vinh"
        }, headers=headers)
        if preview_resp.status_code == 200:
            logger.info(f"-> TTS Preview OK: {preview_resp.json().get('url')}")
            
        voices_resp = await client.get("/ai/voices?provider=fpt", headers=headers)
        if voices_resp.status_code == 200:
            voices = voices_resp.json()
            logger.info(f"-> Fetched {len(voices)} FPT Voices")
            for v in voices:
                if v["preview_url"]:
                    logger.info(f"   Voice {v['voice_code']} has preview: {v['preview_url']}")

        seo_resp = await client.post(f"/articles/{article_id}/ai-seo/generate", headers=headers)
        if seo_resp.status_code == 200:
            logger.info(f"-> Generated SEO: {seo_resp.json()}")
        else:
            logger.warning(f"-> AI SEO Generation skipped or failed: {seo_resp.text}")
            
        logger.info("5. Submit Article to Review (DRAFT -> PENDING)")
        submit_resp = await client.post(f"/articles/{article_id}/submit", headers=headers)
        if submit_resp.status_code != 200:
            logger.error(f"Submit failed: {submit_resp.text}")
            return
        logger.info(f"-> Article Status changed to: {submit_resp.json()['status']}")
        
        logger.info("6. Admin Approves Article (PENDING -> PUBLISHED)")
        approve_resp = await client.post(f"/articles/{article_id}/approve", headers=headers)
        if approve_resp.status_code != 200:
            logger.error(f"Approve failed: {approve_resp.text}")
            return
        logger.info(f"-> Article Status changed to: {approve_resp.json()['status']}")
        
        logger.info("7. Verify Workflow Logs")
        logs_resp = await client.get(f"/articles/{article_id}/workflow-logs", headers=headers)
        if logs_resp.status_code == 200:
            logs = logs_resp.json()
            logger.info(f"-> Found {len(logs)} workflow logs.")
            for log in logs:
                logger.info(f"   - Action: {log['action']} | New Status: {log['to_status']} | At: {log['created_at']}")
        else:
            logger.error(f"Failed to fetch workflow logs: {logs_resp.text}")
            
        logger.info("8. Verify Generated Audio (Wait 6s for background worker)")
        await asyncio.sleep(6.0)
        async with SessionLocal() as db:
            from app.modules.ai.models import ArticleAudio
            audio_query = await db.execute(select(ArticleAudio).where(ArticleAudio.article_id == article_id))
            audios = audio_query.scalars().all()
            logger.info(f"-> Found {len(audios)} Generated Audio files.")
            for a in audios:
                logger.info(f"   - Voice: {a.voice_code} | URL: {a.audio_url}")
            
        logger.info("API A-Z Flow Completed Successfully!")

if __name__ == "__main__":
    asyncio.run(test_api_flow())
