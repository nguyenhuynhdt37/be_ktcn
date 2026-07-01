import asyncio
from sqlalchemy import text
from app.core.database import engine

# Quy tắc ánh xạ danh mục:
# Key là từ khóa trong tiêu đề bài viết (viết thường).
# Value là category_id tương ứng.
MAP_RULES = {
    # 1. Lịch tuần:
    "lịch công tác": "3805d654-d228-4cf1-ab96-e3a76344db85",
    "lịch tuần": "3805d654-d228-4cf1-ab96-e3a76344db85",
    
    # 2. Bộ môn Điện tử Viễn thông:
    "viễn thông": "7d2e5574-a908-426c-aed4-0178e0a21f06",
    "icce": "7d2e5574-a908-426c-aed4-0178e0a21f06",
    
    # 3. Bộ môn Kỹ thuật điều khiển và tự động hóa:
    "tự động hóa": "ba59b5eb-172f-4e6b-b111-b1359d7e5914",
    "điều khiển": "ba59b5eb-172f-4e6b-b111-b1359d7e5914",
    
    # 4. Bộ môn Kỹ thuật điện - điện tử:
    "điện, điện tử": "f95d2056-9175-4469-a8c6-bab3aca3c71a",
    "điện-điện tử": "f95d2056-9175-4469-a8c6-bab3aca3c71a",
    
    # 5. Bộ môn Công nghệ kỹ thuật ô tô:
    "ô tô": "432311dd-b2a9-4c24-b8a2-9e6986e79ada",
    "vinfast": "432311dd-b2a9-4c24-b8a2-9e6986e79ada",
    
    # 6. Bộ môn Hệ thống và Mạng máy tính (CNTT):
    "công nghệ thông tin": "05e6ac54-0b54-44c6-bf76-39d4d05ef0c2",
    "mạng máy tính": "05e6ac54-0b54-44c6-bf76-39d4d05ef0c2",
    "cntt": "05e6ac54-0b54-44c6-bf76-39d4d05ef0c2",
    
    # 7. Chức năng nhiệm vụ:
    "chức năng, nhiệm vụ": "a41bf474-295a-4b89-859e-ebd087d81b48",
    
    # 8. Đoàn thanh niên và Hội sinh viên:
    "đoàn viện": "d95443a8-87d0-4462-a072-66b0a0c2d7d1",
    "thành niên": "d95443a8-87d0-4462-a072-66b0a0c2d7d1",
    "đại hội": "d95443a8-87d0-4462-a072-66b0a0c2d7d1",
    "nhớ bác": "d95443a8-87d0-4462-a072-66b0a0c2d7d1",
    "khởi nghiệp": "d95443a8-87d0-4462-a072-66b0a0c2d7d1",
    "tân sinh viên": "d95443a8-87d0-4462-a072-66b0a0c2d7d1",
    "tuổi trẻ": "d95443a8-87d0-4462-a072-66b0a0c2d7d1",
    
    # 9. Tuyển sinh / Thông báo chung:
    "tuyển sinh": "108ca91a-7773-4c3c-ba1c-1d48188ad0c5",
    "xét tốt nghiệp": "108ca91a-7773-4c3c-ba1c-1d48188ad0c5",
    "học vụ": "108ca91a-7773-4c3c-ba1c-1d48188ad0c5",
    "đánh giá năng lực": "108ca91a-7773-4c3c-ba1c-1d48188ad0c5",
}

# Danh mục mặc định cho các bài còn lại (Tin tức học tập):
DEFAULT_CATEGORY_ID = "92fd3d38-e4e8-4e8a-88bc-b9b26bec2572"

async def auto_map():
    async with engine.begin() as conn:
        print("🚀 Khởi chạy công cụ tự động ánh xạ lại danh mục cho bài viết...")
        
        # 1. Lấy tất cả articles chưa có category_id hoặc tất cả articles để map lại hoàn toàn
        res = await conn.execute(text("SELECT id, title FROM articles;"))
        articles = res.fetchall()
        print(f"📊 Tìm thấy {len(articles)} bài viết trong cơ sở dữ liệu.")
        
        mapped_count = 0
        for aid, title in articles:
            target_cat_id = None
            title_lower = title.lower()
            
            # Quét qua các quy tắc map
            for keyword, cid in MAP_RULES.items():
                if keyword in title_lower:
                    target_cat_id = cid
                    break
            
            # Nếu không khớp quy tắc nào, gán vào Tin tức học tập
            if not target_cat_id:
                target_cat_id = DEFAULT_CATEGORY_ID
                
            # Cập nhật DB
            await conn.execute(
                text(f"UPDATE articles SET category_id = '{target_cat_id}' WHERE id = '{aid}';")
            )
            mapped_count += 1
            
        print(f"🎉 Đã ánh xạ và cập nhật thành công {mapped_count} bài viết!")

if __name__ == "__main__":
    asyncio.run(auto_map())
