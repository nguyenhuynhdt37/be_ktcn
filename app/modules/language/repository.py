import uuid
from datetime import datetime, UTC
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.repositories.base import BaseRepository
from app.modules.language.models import Language
from app.modules.language.schemas import LanguageCreate, LanguageUpdate


class LanguageRepository(BaseRepository[Language, LanguageCreate, LanguageUpdate]):
    """
    Repository quản lý các truy vấn CRUD trên bảng languages.
    """

    def __init__(self):
        super().__init__(Language)

    async def get_all(self, db: AsyncSession, show_deleted: bool = False) -> list[Language]:
        """
        Lấy toàn bộ ngôn ngữ, sắp xếp theo sort_order.
        """
        query = select(self.model)
        if not show_deleted:
            query = query.where(self.model.deleted_at.is_(None))
        query = query.order_by(self.model.sort_order.asc(), self.model.created_at.asc())
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_active(self, db: AsyncSession) -> list[Language]:
        """
        Lấy các ngôn ngữ đang hoạt động và chưa bị xóa mềm.
        """
        query = (
            select(self.model)
            .where(
                self.model.is_active == True,
                self.model.deleted_at.is_(None)
            )
            .order_by(self.model.sort_order.asc(), self.model.created_at.asc())
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_default(self, db: AsyncSession) -> Language | None:
        """
        Lấy ngôn ngữ mặc định (chưa bị xóa mềm).
        """
        query = (
            select(self.model)
            .where(
                self.model.is_default == True,
                self.model.deleted_at.is_(None)
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id(self, db: AsyncSession, id: uuid.UUID) -> Language | None:
        """
        Lấy chi tiết ngôn ngữ theo ID (chưa bị xóa mềm).
        """
        query = (
            select(self.model)
            .where(
                self.model.id == id,
                self.model.deleted_at.is_(None)
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_code(self, db: AsyncSession, code: str) -> Language | None:
        """
        Lấy ngôn ngữ theo code (chưa bị xóa mềm).
        """
        query = (
            select(self.model)
            .where(
                self.model.code == code.strip().lower(),
                self.model.deleted_at.is_(None)
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def exists(self, db: AsyncSession, code: str, exclude_id: Optional[uuid.UUID] = None) -> bool:
        """
        Kiểm tra xem code ngôn ngữ đã tồn tại chưa (gồm cả bản ghi đã bị xóa mềm, loại trừ ID nếu được chỉ định).
        """
        query = select(self.model).where(
            self.model.code == code.strip().lower()
        )
        if exclude_id:
            query = query.where(self.model.id != exclude_id)
        result = await db.execute(query)
        return result.scalar_one_or_none() is not None

    async def soft_delete(self, db: AsyncSession, id: uuid.UUID) -> Language | None:
        """
        Xóa mềm ngôn ngữ theo ID.
        """
        db_obj = await self.get_by_id(db, id)
        if db_obj:
            db_obj.deleted_at = datetime.now(UTC)
            db.add(db_obj)
            await db.flush()
        return db_obj

    async def restore(self, db: AsyncSession, id: uuid.UUID) -> Language | None:
        """
        Khôi phục ngôn ngữ đã bị xóa mềm.
        """
        # Cần lấy cả bản ghi bị xóa mềm
        query = select(self.model).where(self.model.id == id)
        result = await db.execute(query)
        db_obj = result.scalar_one_or_none()
        if db_obj and db_obj.deleted_at is not None:
            db_obj.deleted_at = None
            db.add(db_obj)
            await db.flush()
        return db_obj

    async def enable(self, db: AsyncSession, id: uuid.UUID) -> Language | None:
        """
        Kích hoạt hoạt động cho ngôn ngữ.
        """
        db_obj = await self.get_by_id(db, id)
        if db_obj:
            db_obj.is_active = True
            db.add(db_obj)
            await db.flush()
        return db_obj

    async def disable(self, db: AsyncSession, id: uuid.UUID) -> Language | None:
        """
        Ngưng kích hoạt hoạt động cho ngôn ngữ.
        """
        db_obj = await self.get_by_id(db, id)
        if db_obj:
            db_obj.is_active = False
            db.add(db_obj)
            await db.flush()
        return db_obj

    async def set_default(self, db: AsyncSession, id: uuid.UUID) -> Language | None:
        """
        Đặt ngôn ngữ làm mặc định. Đặt các ngôn ngữ khác thành không mặc định.
        Ngôn ngữ mặc định cũng sẽ tự động được kích hoạt (is_active = True).
        """
        db_obj = await self.get_by_id(db, id)
        if db_obj:
            # 1. Reset all to is_default = False
            reset_query = (
                update(self.model)
                .where(self.model.deleted_at.is_(None))
                .values(is_default=False)
            )
            await db.execute(reset_query)

            # 2. Set default for this language and ensure it is active
            db_obj.is_default = True
            db_obj.is_active = True
            db.add(db_obj)
            await db.flush()
        return db_obj


language_repository = LanguageRepository()
