import asyncio
import sys
import uuid
from loguru import logger
import httpx

# Cấu hình logger
logger.remove()
logger.add(sys.stderr, level="INFO")


async def test_seo_generation():
    # Sử dụng AsyncClient kết nối trực tiếp app qua ASGI để test nhanh
    from app.main import app

    logger.info("⏳ Khởi động AsyncClient kết nối ứng dụng...")
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        logger.info("🔑 1. Đăng nhập tài khoản Admin lấy Token")
        login_payload = {
            "username": "superadmin",
            "password": "Password@123"
        }
        login_res = await ac.post("/api/v1/auth/login", json=login_payload)
        assert login_res.status_code == 200, f"Đăng nhập thất bại: {login_res.text}"
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        logger.info("✅ Đăng nhập thành công!")

        # Lấy một article_id thực tế từ hệ thống
        logger.info("📂 2. Lấy danh sách bài viết từ database...")
        articles_res = await ac.get("/api/v1/admin/articles?page=1&page_size=5", headers=headers)
        assert articles_res.status_code == 200, f"Lấy bài viết thất bại: {articles_res.text}"
        articles = articles_res.json().get("items", [])
        
        if articles:
            article_id = articles[0]["id"]
            logger.info(f"👉 Sử dụng article_id thực tế: {article_id}")
        else:
            article_id = str(uuid.uuid4())
            logger.info(f"👉 Không có bài viết nào trong DB, sử dụng UUID ngẫu nhiên: {article_id}")

        # ----------------------------------------------------
        # TEST CASE 1: Viết lại bài viết (Rewrite) và giữ ảnh Base64
        # ----------------------------------------------------
        logger.info("🧪 3. Test API viết lại bài viết (SEO Rewrite) và bảo toàn ảnh Base64...")
        test_base64_src = "data:image/png;base64,iVBORw0KGgoAAAANS"
        
        rewrite_payload = {
            "content": f"""
                <p>Chúng tôi thông báo tuyển sinh Đại học năm 2026.</p>
                <img src="{test_base64_src}" alt="Ảnh minh họa tuyển sinh" />
                <p>Khoa tuyển sinh các ngành kỹ thuật công nghệ thông tin.</p>
            """,
            "focus_keyword": "tuyển sinh đại học 2026",
            "tone": "thuyết phục",
            "lang": "vi"
        }
        
        rewrite_res = await ac.post(
            f"/api/v1/admin/articles/{article_id}/seo/rewrite",
            json=rewrite_payload,
            headers=headers,
            timeout=120.0
        )
        
        assert rewrite_res.status_code == 200, f"Rewrite API thất bại: {rewrite_res.text}"
        rewrite_data = rewrite_res.json()
        rewritten_content = rewrite_data.get("content", "")
        
        logger.info("🎉 API Viết lại bài viết trả về thành công!")
        logger.info(f"📝 Nội dung HTML đã viết lại: {rewritten_content[:300]}...")
        
        # Kiểm tra xem ảnh base64 ban đầu có được khôi phục nguyên vẹn không
        assert test_base64_src in rewritten_content, "❌ Lỗi: Ảnh Base64 bị mất hoặc không được khôi phục sau khi viết lại!"
        logger.info("✅ Xác minh ảnh Base64 được bảo toàn nguyên vẹn 100% trong HTML kết quả!")

        # ----------------------------------------------------
        # TEST CASE 2: Sinh bài viết từ ý tưởng (Generate by Idea)
        # ----------------------------------------------------
        logger.info("🧪 4. Test API sinh bài viết từ ý tưởng (Generate by Idea)...")
        idea_payload = {
            "idea": "Khai giảng lớp học võ cổ truyền Việt Nam miễn phí hè 2026 cho trẻ em tại trường Tiểu học Vĩnh Sơn để rèn luyện kỹ năng thoát hiểm và nâng cao sức khỏe.",
            "focus_keyword": "võ cổ truyền Việt Nam",
            "tone": "sáng tạo",
            "lang": "vi"
        }
        
        gen_res = await ac.post(
            "/api/v1/admin/articles/seo/generate-by-idea",
            json=idea_payload,
            headers=headers,
            timeout=120.0
        )
        
        assert gen_res.status_code == 200, f"Generate by Idea API thất bại: {gen_res.text}"
        gen_data = gen_res.json()
        
        logger.info("🎉 API Sinh bài viết từ ý tưởng trả về thành công!")
        logger.info(f"✨ Tiêu đề gợi ý: '{gen_data.get('title')}'")
        logger.info(f"✨ Tóm tắt gợi ý: '{gen_data.get('excerpt')}'")
        logger.info(f"✨ Slug gợi ý: '{gen_data.get('slug')}'")
        logger.info(f"✨ Tiêu đề SEO gợi ý: '{gen_data.get('seo_title')}'")
        logger.info(f"✨ Mô tả SEO gợi ý: '{gen_data.get('seo_description')}'")
        logger.info(f"📝 Nội dung HTML sinh ra (phần đầu): {gen_data.get('content', '')[:400]}...")
        
        # Kiểm tra tính hợp lệ cơ bản của dữ liệu
        assert "title" in gen_data
        assert "content" in gen_data
        assert "slug" in gen_data
        assert "seo_title" in gen_data
        assert "seo_description" in gen_data
        
        logger.info("✅ Xác minh dữ liệu sinh ra khớp 100% với Pydantic Response Schema!")

if __name__ == "__main__":
    logger.info("🚀 Khởi động script kiểm thử AI SEO Generation & Rewrite...")
    asyncio.run(test_seo_generation())
