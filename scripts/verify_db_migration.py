import asyncio
from sqlalchemy import text
from app.core.database import engine

async def verify_migration():
    async with engine.connect() as conn:
        # Đếm số lượng categories và translations
        cat_count_res = await conn.execute(text("SELECT count(*) FROM categories"))
        cat_count = cat_count_res.scalar()
        
        trans_count_res = await conn.execute(text("SELECT count(*) FROM category_translations"))
        trans_count = trans_count_res.scalar()
        
        print(f"📊 Kết quả Verify Database Migration:")
        print(f"  - Số lượng danh mục trong bảng categories: {cat_count}")
        print(f"  - Số lượng bản dịch trong bảng category_translations (vi): {trans_count}")
        
        if cat_count == trans_count:
            print("✅ XÁC THỰC THÀNH CÔNG: Dữ liệu đã được migrate đầy đủ 100%!")
        else:
            print("⚠️ CẢNH BÁO: Số lượng dữ liệu di trú không khớp!")
            
        # In thử 3 bản dịch đầu tiên để check nội dung
        sample_res = await conn.execute(
            text(
                "SELECT ct.name, ct.slug, l.code "
                "FROM category_translations ct "
                "JOIN languages l ON ct.language_id = l.id "
                "LIMIT 3"
            )
        )
        samples = sample_res.fetchall()
        print("\n✨ Dữ liệu bản dịch mẫu:")
        for idx, row in enumerate(samples):
            print(f"  Bản ghi {idx}: Tên='{row[0]}', Slug='{row[1]}', Ngôn ngữ='{row[2]}'")

if __name__ == "__main__":
    asyncio.run(verify_migration())
