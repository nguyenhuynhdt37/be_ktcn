import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.academic_title.models import AcademicTitle, AcademicTitleTranslation


class AcademicTitleService:
    def _apply_translation(self, item: AcademicTitle, lang: str = "vi") -> AcademicTitle:
        """Dịch phẳng động cho AcademicTitle."""
        matched = None
        for t in item.translations:
            if t.language.code == lang:
                matched = t
                break
        if not matched and lang != "vi":
            for t in item.translations:
                if t.language.code == "vi":
                    matched = t
                    break
        if not matched and item.translations:
            matched = item.translations[0]

        item.name = matched.name if matched else ""
        item.abbreviation = matched.abbreviation if matched else None
        return item

    async def list_academic_titles(
        self,
        db: AsyncSession,
        is_active: Optional[bool] = None,
        lang: str = "vi"
    ) -> List[AcademicTitle]:
        stmt = (
            select(AcademicTitle)
            .where(AcademicTitle.deleted_at.is_(None))
            .options(
                selectinload(AcademicTitle.translations)
            )
            .order_by(AcademicTitle.sort_order.asc(), AcademicTitle.created_at.desc())
        )
        if is_active is not None:
            stmt = stmt.where(AcademicTitle.is_active == is_active)

        result = await db.execute(stmt)
        items = result.scalars().all()

        for item in items:
            self._apply_translation(item, lang=lang)

        return list(items)
