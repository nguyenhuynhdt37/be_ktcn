import asyncio
import uuid
from sqlalchemy import select
from app.core.database import SessionLocal
from app.modules.category.service import category_service
from app.modules.category.models import Category
from app.modules.article.models import Article
from app.modules.auth.models import User
from app.main import app

async def test_count():
    async with SessionLocal() as db:
        # 1. Lấy một category bất kỳ đang ACTIVE
        stmt = select(Category).where(Category.deleted_at.is_(None)).limit(1)
        res = await db.execute(stmt)
        category = res.scalar_one_or_none()
        if not category:
            print("❌ Không có category nào trong DB để test!")
            return
            
        print(f"Testing with Category: {category.id}")
        
        # 2. Tạo một bài viết nháp gán cho category này
        article = Article(
            title="Bài viết test count logic",
            slug=f"bai-viet-test-count-{uuid.uuid4().hex[:6]}",
            content="Nội dung bài viết test",
            category_id=category.id
        )
        db.add(article)
        await db.flush() # flush để lưu tạm vào transaction
        
        # 3. Gọi hàm đếm của service
        categories = await category_service.list_categories(db)
        target = next((c for c in categories if c.id == category.id), None)
        print(f"  - list_categories count for {category.id}: {target.article_count if target else 'Not found'}")
        
        tree = await category_service.get_category_tree(db)
        
        def find_in_tree(nodes, cid):
            for n in nodes:
                if n.id == cid:
                    return n
                if n.children:
                    found = find_in_tree(n.children, cid)
                    if found:
                        return found
            return None
            
        target_node = find_in_tree(tree, category.id)
        print(f"  - get_category_tree count for {category.id}: {target_node.article_count if target_node else 'Not found'}")
        
        # rollback để không lưu bài viết test vào DB thật
        await db.rollback()
        print("🧹 Cleaned up (rolled back transaction).")

if __name__ == "__main__":
    asyncio.run(test_count())
