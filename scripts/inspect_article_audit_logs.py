import asyncio
import json
from sqlalchemy import text
from app.core.database import engine

async def inspect_article_audit_logs():
    async with engine.connect() as conn:
        print("🔍 Đang tìm kiếm thông tin articles trong audit_logs...")
        
        # 1. Truy vấn các action liên quan đến article
        query = text(
            "SELECT id, action, target_type, target_id, changes, created_at "
            "FROM audit_logs "
            "WHERE target_type = 'article' OR action LIKE '%ARTICLE%' "
            "ORDER BY created_at DESC LIMIT 20;"
        )
        try:
            res = await conn.execute(query)
            rows = res.fetchall()
            print(f"✅ Tìm thấy {len(rows)} bản ghi audit log liên quan đến Article (gần nhất).")
            
            for row in rows:
                log_id, action, target_type, target_id, changes_raw, created_at = row
                target_id_str = str(target_id) if target_id else None
                
                changes = {}
                if changes_raw:
                    if isinstance(changes_raw, str):
                        try:
                            changes = json.loads(changes_raw)
                        except:
                            changes = {}
                    elif isinstance(changes_raw, dict):
                        changes = changes_raw
                
                print(f"  - Action: {action}, TargetID: {target_id_str}, CreatedAt: {created_at}")
                # Chỉ in ra title và category_id/category trong changes để tránh quá dài
                filtered_changes = {k: v for k, v in changes.items() if k in ("title", "category_id", "category")}
                print(f"    Changes: {filtered_changes}")
                
        except Exception as e:
            print(f"❌ Lỗi khi truy vấn audit_logs: {str(e)}")

if __name__ == "__main__":
    asyncio.run(inspect_article_audit_logs())
