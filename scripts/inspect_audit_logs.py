import asyncio
import json
from sqlalchemy import text
from app.core.database import engine

async def inspect_audit_logs():
    async with engine.connect() as conn:
        print("🔍 Đang tìm kiếm thông tin categories trong audit_logs...")
        
        # 1. Truy vấn các action liên quan đến category
        query = text(
            "SELECT id, action, target_type, target_id, changes, created_at "
            "FROM audit_logs "
            "WHERE target_type = 'category' OR action LIKE '%CATEGORY%' "
            "ORDER BY created_at ASC;"
        )
        try:
            res = await conn.execute(query)
            rows = res.fetchall()
            print(f"✅ Tìm thấy {len(rows)} bản ghi audit log liên quan đến Category.")
            
            categories_history = {}
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
                print(f"    Changes: {changes}")
                
                if action in ("CATEGORY_CREATED", "CATEGORY_UPDATED"):
                    if target_id_str:
                        if target_id_str not in categories_history:
                            categories_history[target_id_str] = {}
                        categories_history[target_id_str].update(changes)
            
            print(f"\n📂 Tổng số danh mục có thể khôi phục: {len(categories_history)}")
            for cid, cdata in list(categories_history.items())[:5]:
                print(f"  - ID: {cid} -> Data: {cdata}")
                
        except Exception as e:
            print(f"❌ Lỗi khi truy vấn audit_logs: {str(e)}")

if __name__ == "__main__":
    asyncio.run(inspect_audit_logs())
