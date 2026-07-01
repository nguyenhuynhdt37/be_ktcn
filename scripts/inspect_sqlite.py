import sqlite3
import os

def inspect_sqlite():
    db_path = "app.db"
    if not os.path.exists(db_path):
        print(f"❌ File {db_path} không tồn tại!")
        return
        
    print(f"🔍 Inspecting SQLite database {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Xem danh sách các bảng
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in cursor.fetchall()]
    print(f"  - Các bảng trong SQLite: {tables}")
    
    # 2. Kiểm tra số lượng articles và category_id
    if "articles" in tables:
        cursor.execute("SELECT count(*) FROM articles;")
        print(f"  - Số lượng bài viết trong SQLite: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT count(*) FROM articles WHERE category_id IS NOT NULL;")
        print(f"  - Số lượng bài viết có category_id trong SQLite: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT id, title, category_id FROM articles WHERE category_id IS NOT NULL LIMIT 5;")
        rows = cursor.fetchall()
        for r in rows:
            print(f"    + ID: {r[0]}, Title: {r[1]}, Category ID: {r[2]}")
            
    conn.close()

if __name__ == "__main__":
    inspect_sqlite()
