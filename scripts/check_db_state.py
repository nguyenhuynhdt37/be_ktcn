import asyncio
from sqlalchemy import text
from app.core.database import engine

async def check_db_state():
    async with engine.connect() as conn:
        print("🔍 Đang kiểm tra trạng thái cơ sở dữ liệu...")
        
        # 1. Kiểm tra số lượng articles
        try:
            res = await conn.execute(text("SELECT count(*) FROM articles;"))
            articles_count = res.scalar()
            print(f"  - Số lượng bài viết (articles): {articles_count}")
        except Exception as e:
            print(f"  - Lỗi khi truy vấn articles: {str(e)}")
            
        # 2. Lấy danh sách category_id từ articles (nếu còn)
        try:
            res = await conn.execute(text("SELECT DISTINCT category_id FROM articles WHERE category_id IS NOT NULL;"))
            cat_ids = [str(row[0]) for row in res.fetchall()]
            print(f"  - Số lượng category_id duy nhất đang được liên kết trong bài viết: {len(cat_ids)}")
            if cat_ids:
                print(f"  - Các category_id: {cat_ids[:5]}...")
        except Exception as e:
            print(f"  - Lỗi khi truy vấn category_id từ articles: {str(e)}")

        # 3. Kiểm tra xem có bảng sao lưu tạm thời nào không
        try:
            res = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public';"))
            tables = [row[0] for row in res.fetchall()]
            print(f"  - Danh sách các bảng hiện có: {tables}")
        except Exception as e:
            print(f"  - Lỗi khi lấy danh sách bảng: {str(e)}")

if __name__ == "__main__":
    asyncio.run(check_db_state())
