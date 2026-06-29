import asyncio
import uuid
import random
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, delete

from app.core.database import SessionLocal
from app.modules.article.models import Article, ArticleTag, ArticleStatus
from app.modules.auth.models import User
from app.modules.category.models import Category
from app.modules.tag.models import Tag

# Danh sách URL ảnh mẫu chất lượng cao từ Unsplash để xoay vòng
UNSPLASH_IMAGES = [
    "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?auto=format&fit=crop&q=80&w=400",
    "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&q=80&w=400",
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&q=80&w=400",
    "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&q=80&w=400",
    "https://images.unsplash.com/photo-1531297484001-80022131f5a1?auto=format&fit=crop&q=80&w=400",
    "https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&q=80&w=400",
    "https://images.unsplash.com/photo-1488590528505-98d2b5aba04b?auto=format&fit=crop&q=80&w=400"
]

async def seed_data():
    print("=== BẮT ĐẦU SEED 100+ DỮ LIỆU MẪU ĐỂ TEST PHÂN TRANG ===")
    async with SessionLocal() as db:
        
        # 1. Tìm tác giả test (nguyenhuynhdt37@gmail.com)
        user_stmt = select(User).where(User.username == "nguyenhuynhdt37@gmail.com")
        user_res = await db.execute(user_stmt)
        author = user_res.scalars().first()
        if not author:
            print("Không tìm thấy user 'nguyenhuynhdt37@gmail.com'. Vui lòng tạo tài khoản trước.")
            return

        # Đảm bảo tác giả có thông tin avatar và họ tên
        author.avatar_url = "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&q=80&w=200"
        author.full_name = "Nguyễn Huỳnh"
        db.add(author)

        # 2. Tạo các danh mục mẫu (Categories)
        categories_data = [
            {"name": "Tin tức học tập", "slug": "tin-tuc-hoc-tap", "desc": "Các tin tức về học tập, giáo trình, lịch thi"},
            {"name": "Hoạt động ngoại khóa", "slug": "hoat-dong-ngoai-khoa", "desc": "Các hoạt động tình nguyện, câu lạc bộ, thể thao"},
            {"name": "Thông báo chung", "slug": "thong-bao-chung", "desc": "Các thông báo chính thức từ ban giám hiệu"}
        ]
        
        categories_dict = {}
        category_list = []
        for cat_data in categories_data:
            stmt = select(Category).where(Category.slug == cat_data["slug"])
            res = await db.execute(stmt)
            cat = res.scalars().first()
            if not cat:
                cat = Category(
                    name=cat_data["name"],
                    slug=cat_data["slug"],
                    description=cat_data["desc"],
                    status="ACTIVE"
                )
                db.add(cat)
                await db.flush()
            categories_dict[cat_data["slug"]] = cat.id
            category_list.append(cat.id)

        # 3. Tạo các Tag mẫu (Tags)
        tags_data = [
            {"name": "Python", "slug": "python", "color": "#3377FF"},
            {"name": "Web Development", "slug": "web-dev", "color": "#FF5733"},
            {"name": "FastAPI", "slug": "fastapi", "color": "#009688"},
            {"name": "Tuyển sinh", "slug": "tuyen-sinh", "color": "#E91E63"},
            {"name": "Học bổng", "slug": "hoc-bong", "color": "#9C27B0"}
        ]

        tags_dict = {}
        tag_list = []
        for tag_data in tags_data:
            stmt = select(Tag).where(Tag.slug == tag_data["slug"])
            res = await db.execute(stmt)
            tag = res.scalars().first()
            if not tag:
                tag = Tag(
                    name=tag_data["name"],
                    slug=tag_data["slug"],
                    color=tag_data["color"],
                    description=f"Thẻ bài viết liên quan đến {tag_data['name']}",
                    is_active=True
                )
                db.add(tag)
                await db.flush()
            tags_dict[tag_data["slug"]] = tag.id
            tag_list.append(tag.id)

        # 4. Xóa sạch các bài viết test cũ bắt đầu bằng "SEED_"
        print("- Đang dọn dẹp các bài viết SEED cũ...")
        await db.execute(delete(Article).where(Article.title.like("SEED_%")))
        await db.flush()

        # 5. Tạo 7 bài viết đặc biệt như ban đầu
        now = datetime.now(timezone.utc)
        special_articles = [
            {
                "title": "SEED_Lập trình hướng đối tượng với Python nâng cao",
                "slug": "seed-python-oop-nang-cao",
                "excerpt": "Tìm hiểu chi tiết các khái niệm OOP trong ngôn ngữ Python từ kế thừa, đa hình, đến các phương thức magic.",
                "thumbnail": "https://images.unsplash.com/photo-1515879218367-8466d910aaa4?auto=format&fit=crop&q=80&w=400",
                "status": ArticleStatus.PUBLISHED,
                "is_featured": True,
                "is_pinned": True,
                "view_count": 340,
                "category": "tin-tuc-hoc-tap",
                "tags": ["python", "web-dev"],
                "publish_delta_hours": -24
            },
            {
                "title": "SEED_Xây dựng RESTful API siêu tốc bằng FastAPI",
                "slug": "seed-fastapi-quickstart",
                "excerpt": "FastAPI là framework hiện đại, có hiệu năng cực cao và giúp viết code nhanh chóng nhờ tận dụng Python Type Hints.",
                "thumbnail": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&q=80&w=400",
                "status": ArticleStatus.PUBLISHED,
                "is_featured": True,
                "is_pinned": False,
                "view_count": 890,
                "category": "tin-tuc-hoc-tap",
                "tags": ["python", "fastapi", "web-dev"],
                "publish_delta_hours": -12
            },
            {
                "title": "SEED_Thông báo nộp hồ sơ xét học bổng kỳ 2 năm học 2025-2026",
                "slug": "seed-thong-bao-hoc-bong-ky-2",
                "excerpt": "Nhà trường chính thức mở cổng nhận hồ sơ xét duyệt học bổng khuyến khích học tập và hỗ trợ khó khăn học kỳ 2.",
                "thumbnail": "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?auto=format&fit=crop&q=80&w=400",
                "status": ArticleStatus.PUBLISHED,
                "is_featured": False,
                "is_pinned": True,
                "view_count": 1200,
                "category": "thong-bao-chung",
                "tags": ["hoc-bong"],
                "publish_delta_hours": -2
            },
            {
                "title": "SEED_Chiến dịch tình nguyện Mùa Hè Xanh năm 2026 chính thức khởi động",
                "slug": "seed-tinh-nguyen-mua-he-xanh-2026",
                "excerpt": "Hội Sinh viên phát động chiến dịch tình nguyện hè tại các tỉnh miền Tây với nhiều công trình dân sinh ý nghĩa.",
                "thumbnail": "https://images.unsplash.com/photo-1559027615-cd4628902d4a?auto=format&fit=crop&q=80&w=400",
                "status": ArticleStatus.PUBLISHED,
                "is_featured": False,
                "is_pinned": False,
                "view_count": 120,
                "category": "hoat-dong-ngoai-khoa",
                "tags": ["web-dev"],
                "publish_delta_hours": -48
            },
            {
                "title": "SEED_Đề án Tuyển sinh Đại học hệ chính quy năm học 2026",
                "slug": "seed-de-an-tuyen-sinh-2026",
                "excerpt": "Thông tin chi tiết về chỉ tiêu tuyển sinh, các tổ hợp xét tuyển và phương thức nộp hồ sơ xét tuyển năm học 2026.",
                "thumbnail": "https://images.unsplash.com/photo-1523050854058-8df90110c9f1?auto=format&fit=crop&q=80&w=400",
                "status": ArticleStatus.SCHEDULED,
                "is_featured": False,
                "is_pinned": False,
                "view_count": 0,
                "category": "thong-bao-chung",
                "tags": ["tuyen-sinh"],
                "publish_delta_hours": 48
            },
            {
                "title": "SEED_Tổng kết giải bóng đá sinh viên Cúp Tứ Hùng 2026",
                "slug": "seed-tong-ket-bong-da-2026",
                "excerpt": "Giải đấu kết thúc tốt đẹp với cúp vô địch thuộc về Liên quân Khoa Công nghệ thông tin và Khoa Điện tử.",
                "thumbnail": "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?auto=format&fit=crop&q=80&w=400",
                "status": ArticleStatus.ARCHIVED,
                "is_featured": False,
                "is_pinned": False,
                "view_count": 450,
                "category": "hoat-dong-ngoai-khoa",
                "tags": [],
                "publish_delta_hours": -72
            },
            {
                "title": "SEED_Bài viết đã xóa nằm trong thùng rác test",
                "slug": "seed-bai-viet-trong-rac",
                "excerpt": "Mô tả bài viết cũ...",
                "thumbnail": "https://images.unsplash.com/photo-1531403009284-440f080d1e12?auto=format&fit=crop&q=80&w=400",
                "status": ArticleStatus.PUBLISHED,
                "is_featured": False,
                "is_pinned": False,
                "view_count": 10,
                "category": "tin-tuc-hoc-tap",
                "tags": [],
                "publish_delta_hours": -120,
                "is_deleted": True
            }
        ]

        for art_data in special_articles:
            publish_time = now + timedelta(hours=art_data["publish_delta_hours"])
            art = Article(
                title=art_data["title"],
                slug=art_data["slug"],
                excerpt=art_data["excerpt"],
                content=f"Nội dung chi tiết của bài viết '{art_data['title']}'",
                thumbnail_object_key=art_data["thumbnail"],
                cover_object_key="https://images.unsplash.com/photo-1557804506-669a67965ba0?auto=format&fit=crop&q=80&w=1200",
                status=art_data["status"],
                is_featured=art_data["is_featured"],
                is_pinned=art_data["is_pinned"],
                view_count=art_data["view_count"],
                publish_at=publish_time,
                published_at=publish_time if art_data["status"] == ArticleStatus.PUBLISHED else None,
                category_id=categories_dict[art_data["category"]],
                author_id=author.id,
                deleted_at=now if art_data.get("is_deleted") else None
            )
            db.add(art)
            await db.flush()
            
            # Gán Tag
            for tag_slug in art_data["tags"]:
                art_tag = ArticleTag(article_id=art.id, tag_id=tags_dict[tag_slug])
                db.add(art_tag)

        print("- Đang tạo thêm 100 bài viết phân trang...")
        # 6. Tạo thêm 100 bài viết mẫu phục vụ phân trang
        for i in range(1, 101):
            # Lùi thời gian publish để sắp xếp desc trông tự nhiên (bài viết mới nhất lên trước)
            publish_time = now - timedelta(minutes=i * 15)
            
            # Chọn ngẫu nhiên danh mục và ảnh
            cat_id = random.choice(category_list)
            img_url = random.choice(UNSPLASH_IMAGES)
            
            # Chọn ngẫu nhiên 0 đến 2 tag
            random_tag_ids = random.sample(tag_list, k=random.randint(0, 2))

            art = Article(
                title=f"SEED_Bài viết phân trang số {i}",
                slug=f"seed-bai-viet-phan-trang-{i}",
                excerpt=f"Đây là tóm tắt ngắn cho bài viết mẫu phân trang số {i}. Phục vụ FE test trang danh sách, chuyển trang.",
                content=f"Đây là nội dung của bài viết phân trang số {i}...",
                thumbnail_object_key=img_url,
                cover_object_key="https://images.unsplash.com/photo-1557804506-669a67965ba0?auto=format&fit=crop&q=80&w=1200",
                status=ArticleStatus.PUBLISHED,
                is_featured=random.choice([True, False, False, False]), # Thỉnh thoảng có bài nổi bật
                is_pinned=False,
                view_count=random.randint(5, 500),
                publish_at=publish_time,
                published_at=publish_time,
                category_id=cat_id,
                author_id=author.id
            )
            db.add(art)
            await db.flush()

            # Liên kết tags
            for t_id in random_tag_ids:
                art_tag = ArticleTag(article_id=art.id, tag_id=t_id)
                db.add(art_tag)

        await db.commit()
    print("=== SEED 100+ DỮ LIỆU MẪU THÀNH CÔNG! ===")

if __name__ == "__main__":
    asyncio.run(seed_data())
