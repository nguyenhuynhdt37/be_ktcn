import asyncio
import sys
from pathlib import Path
from sqlalchemy import select

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.modules.position.models import Position, PositionTranslation
from app.modules.language.models import Language

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
from app.modules.staff.models import Staff, StaffTranslation

async def main():
    async with SessionLocal() as db:
        print("\n================ INSPECT POSITIONS ================")
        stmt = select(Position)
        res = await db.execute(stmt)
        positions = res.scalars().all()
        for p in positions:
            vi_name = next((tr.name for tr in p.translations if tr.language.code == "vi"), "No VI Name")
            en_name = next((tr.name for tr in p.translations if tr.language.code == "en"), "No EN Name")
            print(f"Position ID: {p.id} | Name: {vi_name} ({en_name})")

if __name__ == "__main__":
    asyncio.run(main())
