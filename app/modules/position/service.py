import uuid
from datetime import UTC, datetime
from typing import Optional, Tuple
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import BadRequestException, NotFoundException
from app.modules.position.models import Position, PositionTranslation
from app.modules.position.schemas import PositionCreate, PositionUpdate
from app.modules.language.models import Language


class PositionService:
    async def get_language_map(self, db: AsyncSession) -> dict[str, uuid.UUID]:
        stmt = select(Language).where(Language.is_active == True)
        result = await db.execute(stmt)
        return {lang.code: lang.id for lang in result.scalars().all()}

    def _apply_translation(self, position: Position, lang: str = "vi") -> Position:
        """Gán các thuộc tính động (name, description) dựa trên ngôn ngữ."""
        matched = None
        for t in position.translations:
            if t.language.code == lang:
                matched = t
                break
        if not matched and lang != "vi":
            for t in position.translations:
                if t.language.code == "vi":
                    matched = t
                    break
        if not matched and position.translations:
            matched = position.translations[0]

        position.name = matched.name if matched else ""
        position.description = matched.description if matched else None
        return position

    async def list_positions(
        self,
        db: AsyncSession,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        sort_by: str = "sort_order",
        order: str = "asc",
        page: int = 1,
        page_size: int = 10,
        lang: str = "vi",
    ) -> Tuple[list[Position], int]:
        stmt = select(Position).where(Position.deleted_at.is_(None))

        if is_active is not None:
            stmt = stmt.where(Position.is_active == is_active)

        if search:
            stmt = stmt.join(PositionTranslation).where(
                or_(
                    PositionTranslation.name.ilike(f"%{search}%"),
                    PositionTranslation.description.ilike(f"%{search}%"),
                )
            ).distinct()

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await db.execute(count_stmt)
        total_count = total.scalar() or 0

        # Sort & Pagination
        if sort_by == "name" and search:
            if order == "desc":
                stmt = stmt.order_by(PositionTranslation.name.desc())
            else:
                stmt = stmt.order_by(PositionTranslation.name.asc())
        else:
            sort_attr = getattr(Position, sort_by, Position.sort_order)
            if order == "desc":
                stmt = stmt.order_by(sort_attr.desc())
            else:
                stmt = stmt.order_by(sort_attr.asc())

        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        result = await db.execute(stmt)
        positions = result.scalars().all()

        for pos in positions:
            self._apply_translation(pos, lang=lang)

        return list(positions), total_count

    async def get_position(self, db: AsyncSession, position_id: uuid.UUID, lang: str = "vi") -> Position:
        stmt = select(Position).where(Position.id == position_id, Position.deleted_at.is_(None))
        result = await db.execute(stmt)
        pos = result.scalar_one_or_none()
        if not pos:
            raise NotFoundException("Không tìm thấy chức vụ")
        self._apply_translation(pos, lang=lang)
        return pos

    async def create_position(self, db: AsyncSession, data: PositionCreate) -> Position:
        lang_map = await self.get_language_map(db)

        if "vi" not in data.translations or not data.translations["vi"].name:
            raise BadRequestException("Bản dịch tiếng Việt (vi) là bắt buộc và không được trống tên")

        # Tự động đẩy các position có sort_order >= data.sort_order
        from sqlalchemy import update
        await db.execute(
            update(Position)
            .where(Position.deleted_at.is_(None), Position.sort_order >= data.sort_order)
            .values(sort_order=Position.sort_order + 1)
        )

        pos = Position(
            sort_order=data.sort_order,
            is_active=data.is_active,
        )
        db.add(pos)
        await db.flush()

        for code, trans_data in data.translations.items():
            if code not in lang_map:
                continue
            if not trans_data.name:
                continue

            trans = PositionTranslation(
                position_id=pos.id,
                language_id=lang_map[code],
                name=trans_data.name,
                description=trans_data.description,
            )
            db.add(trans)

        await db.flush()
        stmt = select(Position).where(Position.id == pos.id)
        pos = (await db.execute(stmt)).scalar_one()
        self._apply_translation(pos, lang="vi")
        return pos

    async def update_position(self, db: AsyncSession, position_id: uuid.UUID, data: PositionUpdate) -> Position:
        pos = await self.get_position(db, position_id)
        lang_map = await self.get_language_map(db)

        if data.sort_order is not None and data.sort_order != pos.sort_order:
            old_sort = pos.sort_order
            new_sort = data.sort_order
            from sqlalchemy import update
            if new_sort < old_sort:
                await db.execute(
                    update(Position)
                    .where(
                        Position.deleted_at.is_(None),
                        Position.sort_order >= new_sort,
                        Position.sort_order < old_sort,
                        Position.id != pos.id
                    )
                    .values(sort_order=Position.sort_order + 1)
                )
            else:
                await db.execute(
                    update(Position)
                    .where(
                        Position.deleted_at.is_(None),
                        Position.sort_order > old_sort,
                        Position.sort_order <= new_sort,
                        Position.id != pos.id
                    )
                    .values(sort_order=Position.sort_order - 1)
                )
            pos.sort_order = new_sort
        if data.is_active is not None:
            pos.is_active = data.is_active

        if data.translations is not None:
            for code, trans_data in data.translations.items():
                if code not in lang_map:
                    continue

                matched = None
                for t in pos.translations:
                    if t.language.code == code:
                        matched = t
                        break

                if matched:
                    if trans_data.name:
                        matched.name = trans_data.name
                        matched.description = trans_data.description
                else:
                    if trans_data.name:
                        new_trans = PositionTranslation(
                            position_id=pos.id,
                            language_id=lang_map[code],
                            name=trans_data.name,
                            description=trans_data.description,
                        )
                        db.add(new_trans)

        await db.flush()
        self._apply_translation(pos, lang="vi")
        return pos

    async def delete_position(self, db: AsyncSession, position_id: uuid.UUID) -> None:
        from app.modules.staff.models import Staff
        # Kiểm tra xem có giảng viên nào đang giữ chức vụ này không
        staff_exists = await db.execute(
            select(Staff.id).where(Staff.position_id == position_id, Staff.deleted_at.is_(None))
        )
        if staff_exists.first():
            raise BadRequestException("Không thể xóa chức vụ này vì đang có giảng viên đảm nhiệm")

        pos = await self.get_position(db, position_id)
        pos.deleted_at = datetime.now(UTC)
        await db.flush()

    async def get_stats(self, db: AsyncSession) -> dict:
        from sqlalchemy import func
        pos_total = (await db.execute(select(func.count(Position.id)).where(Position.deleted_at.is_(None)))).scalar() or 0
        pos_active = (await db.execute(select(func.count(Position.id)).where(Position.deleted_at.is_(None), Position.is_active == True))).scalar() or 0
        pos_inactive = pos_total - pos_active
        return {
            "total": pos_total,
            "active": pos_active,
            "inactive": pos_inactive
        }


position_service = PositionService()
