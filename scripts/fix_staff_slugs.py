import asyncio
import sys
import uuid
from pathlib import Path
from sqlalchemy import select
import unicodedata
import re

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.modules.staff.models import Staff

# Import all models to prevent NoReferencedTableError
from app.modules.auth.models import User, RefreshToken, LoginHistory
from app.modules.media.models import MediaItem
from app.modules.academic_title.models import AcademicTitle, AcademicTitleTranslation
from app.modules.degree.models import Degree, DegreeTranslation
from app.modules.banner.models import Banner
from app.modules.ai_hub.models import AIRequestLog
from app.modules.statistics.models import SystemStatistics
from app.modules.consultation.models import ConsultationLead
from app.modules.notification.models import Notification
from app.modules.category.models import Category, CategoryTranslation
from app.modules.menu.models import MenuItem, MenuItemTranslation
from app.modules.article.models import Article
from app.modules.tag.models import Tag
from app.modules.department.models import Department, DepartmentTranslation

def slugify(text: str) -> str:
    text = text.replace('đ', 'd').replace('Đ', 'D')
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    return re.sub(r'[-\s]+', '-', text)

async def main():
    async with SessionLocal() as db:
        print("Sửa lỗi slug của các giảng viên...")
        stmt = select(Staff)
        res = await db.execute(stmt)
        staffs = res.scalars().all()
        
        for s in staffs:
            correct_slug = slugify(s.full_name)
            if s.slug != correct_slug:
                print(f"Đang sửa slug của {s.full_name}: {s.slug} -> {correct_slug}")
                s.slug = correct_slug
                
        await db.commit()
        print("Hoàn tất sửa lỗi slug!")

if __name__ == "__main__":
    asyncio.run(main())
