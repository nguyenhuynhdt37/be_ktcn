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

    async def create_language(self, db: AsyncSession, obj_in: LanguageCreate) -> Language:
        """
        Tạo mới một ngôn ngữ.
        Đảm bảo code duy nhất và xử lý logic ngôn ngữ mặc định.
        """
        # 1. Validate code duy nhất
        code = obj_in.code.strip().lower()
        if await language_repository.exists(db, code):
            raise ConflictException(f"Mã ngôn ngữ '{code}' đã tồn tại")

        # 2. Xử lý logic default language
        if obj_in.is_default:
            # Nếu thiết lập default mới, gỡ bỏ default cũ
            default_lang = await language_repository.get_default(db)
            if default_lang:
                default_lang.is_default = False
                db.add(default_lang)
        else:
            # Nếu đây là ngôn ngữ đầu tiên được tạo, bắt buộc phải là default
            all_langs = await language_repository.get_all(db)
            if not all_langs:
                obj_in.is_default = True

        # 3. Tạo mới qua repo
        lang = await language_repository.create(db, obj_in=obj_in)
        return lang

    async def update_language(
        self, db: AsyncSession, id: uuid.UUID, obj_in: LanguageUpdate
    ) -> Language:
        """
        Cập nhật thông tin ngôn ngữ.
        Đảm bảo các ràng buộc về trạng thái hoạt động và mặc định.
        """
        lang = await self.get_language_by_id(db, id)

        # 1. Không cho disable ngôn ngữ mặc định
        if obj_in.is_active is False and lang.is_default:
            raise BadRequestException("Không thể vô hiệu hóa ngôn ngữ mặc định")

        # 2. Xử lý thay đổi is_default
        if obj_in.is_default is False and lang.is_default:
            raise BadRequestException(
                "Không thể trực tiếp bỏ mặc định ngôn ngữ này. Vui lòng thiết lập ngôn ngữ khác làm mặc định."
            )

        if obj_in.is_default is True and not lang.is_default:
            # Tắt default cũ
            default_lang = await language_repository.get_default(db)
            if default_lang and default_lang.id != id:
                default_lang.is_default = False
                db.add(default_lang)
            # Ngôn ngữ mặc định thì bắt buộc phải hoạt động
            lang.is_active = True

        # 3. Cập nhật qua repo
        updated_lang = await language_repository.update(db, db_obj=lang, obj_in=obj_in)
        return updated_lang

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

    async def delete_language(self, db: AsyncSession, id: uuid.UUID) -> Language:
        """
        Xóa mềm ngôn ngữ.
        Đảm bảo không xóa ngôn ngữ mặc định và ngôn ngữ hệ thống.
        """
        lang = await self.get_language_by_id(db, id)
        if lang.is_default:
            raise BadRequestException("Không thể xóa ngôn ngữ mặc định")
        if lang.is_system:
            raise BadRequestException("Không thể xóa ngôn ngữ hệ thống")
        
        await language_repository.soft_delete(db, id)
        return lang

    async def restore_language(self, db: AsyncSession, id: uuid.UUID) -> Language:
        """
        Khôi phục ngôn ngữ đã bị xóa mềm.
        """
        query = select(Language).where(Language.id == id)
        result = await db.execute(query)
        lang = result.scalar_one_or_none()
        
        if not lang:
            raise NotFoundException("Ngôn ngữ không tồn tại")
        if lang.deleted_at is None:
            return lang
            
        await language_repository.restore(db, id)
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
