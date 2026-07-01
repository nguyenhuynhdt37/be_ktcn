import asyncio
from sqlalchemy import text
from app.core.database import engine

async def remove_lao():
    async with engine.connect() as conn:
        print("🗑️ Đang xóa ngôn ngữ tiếng Lào (lo) khỏi cơ sở dữ liệu...")
        
        # Kiểm tra xem có bản dịch nào đang liên kết với ngôn ngữ lo không
        check_query = text(
            "SELECT count(*) FROM category_translations ct "
            "JOIN languages l ON ct.language_id = l.id "
            "WHERE l.code = 'lo'"
        )
        count_res = await conn.execute(check_query)
        count = count_res.scalar() or 0
        
        if count > 0:
            print(f"⚠️ Phát hiện {count} bản dịch Category đang dùng tiếng Lào.")
            print("Đang tiến hành xóa các bản dịch tiếng Lào trước...")
            delete_trans = text(
                "DELETE FROM category_translations WHERE language_id IN ("
                "SELECT id FROM languages WHERE code = 'lo'"
                ")"
            )
            await conn.execute(delete_trans)
            print("  - Đã xóa xong bản dịch tiếng Lào.")
            
        # Xóa ngôn ngữ
        delete_lang = text("DELETE FROM languages WHERE code = 'lo';")
        await conn.execute(delete_lang)
        print("  - Đã xóa ngôn ngữ 'lo' khỏi bảng languages.")
        
        await conn.commit()
    print("✅ Đã loại bỏ tiếng Lào thành công!")

if __name__ == "__main__":
    asyncio.run(remove_lao())
