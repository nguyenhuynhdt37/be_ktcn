import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, ConflictException, NotFoundException
from app.modules.language.models import Language
from app.modules.language.repository import language_repository
from app.modules.language.schemas import LanguageCreate, LanguageUpdate, LanguageReorderRequest


class LanguageService:
    """
    Service xử lý logic nghiệp vụ và ràng buộc liên quan đến Ngôn ngữ.
    """

    async def list_languages(self, db: AsyncSession, show_deleted: bool = False) -> list[Language]:
        """
        Lấy danh sách tất cả các ngôn ngữ (bao gồm hoặc loại trừ bản ghi xóa mềm).
        """
        return await language_repository.get_all(db, show_deleted=show_deleted)

    async def list_portal_languages(self, db: AsyncSession) -> list[Language]:
        """
        Lấy danh sách các ngôn ngữ đang hoạt động phục vụ Public Portal.
        """
        return await language_repository.get_active(db)

    async def get_language_by_id(self, db: AsyncSession, id: uuid.UUID) -> Language:
        """
        Lấy thông tin chi tiết của ngôn ngữ theo ID. Báo lỗi nếu không tìm thấy.
        """
        lang = await language_repository.get_by_id(db, id)
        if not lang:
            raise NotFoundException("Ngôn ngữ không tồn tại hoặc đã bị xóa")
        return lang

    async def enable_language(self, db: AsyncSession, id: uuid.UUID) -> Language:
        """
        Kích hoạt hoạt động cho ngôn ngữ.
        """
        lang = await self.get_language_by_id(db, id)
        await language_repository.enable(db, id)
        return lang

    async def disable_language(self, db: AsyncSession, id: uuid.UUID) -> Language:
        """
        Ngưng kích hoạt hoạt động cho ngôn ngữ.
        Đảm bảo không disable ngôn ngữ mặc định.
        """
        lang = await self.get_language_by_id(db, id)
        if lang.is_default:
            raise BadRequestException("Không thể vô hiệu hóa ngôn ngữ mặc định")
        
        await language_repository.disable(db, id)
        return lang

    async def set_default_language(self, db: AsyncSession, id: uuid.UUID) -> Language:
        """
        Thiết lập ngôn ngữ làm mặc định.
        """
        lang = await self.get_language_by_id(db, id)
        await language_repository.set_default(db, id)
        return lang

    async def reorder_languages(self, db: AsyncSession, data: LanguageReorderRequest) -> None:
        """
        Cập nhật đồng loạt vị trí kéo thả của danh sách ngôn ngữ (sort_order).
        """
        ids = [item.id for item in data.items]
        query = select(Language).where(Language.id.in_(ids))
        res = await db.execute(query)
        langs = {lang.id: lang for lang in res.scalars().all()}

        for reorder_item in data.items:
            lang = langs.get(reorder_item.id)
            if not lang:
                raise NotFoundException(f"Không tìm thấy ngôn ngữ có ID {reorder_item.id}")
            lang.sort_order = reorder_item.sort_order
            db.add(lang)
        
        await db.flush()


language_service = LanguageService()
