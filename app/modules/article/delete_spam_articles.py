import asyncio
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

# Import đầy đủ các model để SQLAlchemy registry cấu hình mapper đầy đủ
from app.modules.media.models import MediaItem
from app.modules.auth.models import User
from app.modules.category.models import Category, CategoryTranslation
from app.modules.tag.models import Tag, TagTranslation
from app.modules.article.models import Article, ArticleTranslation
from app.modules.language.models import Language

from app.core.database import get_db

SPAM_TITLES = {
    "sinh viên",
    "tuyển dụng",
    "nghiên cứu khoa học",
    "tuyển sinh",
    "đào tạo",
    "đào tạo",
    "thông báo",
    "lịch tuần",
    "quốc tế",
    "trong nước"
}

async def delete_spam():
    db_gen = get_db()
    db = await anext(db_gen)
    
    try:
        # 1. Tìm các bài viết rác
        stmt_articles = (
            select(Article)
            .options(
                selectinload(Article.translations).selectinload(ArticleTranslation.language)
            )
        )
        articles = (await db.execute(stmt_articles)).scalars().all()
        
        spam_ids = []
        for art in articles:
            vi_trans = next((t for t in art.translations if t.language.code == 'vi'), None)
            title = vi_trans.title.strip() if vi_trans else ""
            title_lower = title.lower()
            
            if title_lower in SPAM_TITLES:
                spam_ids.append(art.id)
        
        print(f"Tìm thấy {len(spam_ids)} bài viết rác cần xóa.")
        
        if len(spam_ids) > 0:
            # 2. Xóa các bài viết rác (các bảng liên quan translations và tags liên kết sẽ tự động cascade delete)
            delete_stmt = delete(Article).where(Article.id.in_(spam_ids))
            result = await db.execute(delete_stmt)
            await db.commit()
            print(f"Đã xóa thành công {result.rowcount} bài viết khỏi cơ sở dữ liệu.")
        else:
            print("Không tìm thấy bài viết rác nào để xóa.")
            
    except Exception as e:
        await db.rollback()
        print(f"Lỗi khi xóa bài viết rác: {e}")
        raise e
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(delete_spam())
