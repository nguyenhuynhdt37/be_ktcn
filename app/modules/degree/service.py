import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.degree.models import Degree, DegreeTranslation


class DegreeService:
    def _apply_translation(self, item: Degree, lang: str = "vi") -> Degree:
        """Dịch phẳng động cho Degree."""
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

    async def list_degrees(
        self,
        db: AsyncSession,
        is_active: Optional[bool] = None,
        lang: str = "vi"
    ) -> List[Degree]:
        stmt = (
            select(Degree)
            .where(Degree.deleted_at.is_(None))
            .options(
                selectinload(Degree.translations)
            )
            .order_by(Degree.sort_order.asc(), Degree.created_at.desc())
        )
        if is_active is not None:
            stmt = stmt.where(Degree.is_active == is_active)

        result = await db.execute(stmt)
        items = result.scalars().all()

        for item in items:
            self._apply_translation(item, lang=lang)

        return list(items)
