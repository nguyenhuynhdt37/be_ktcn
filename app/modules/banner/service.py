import uuid
from datetime import datetime, UTC
from typing import Optional
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException
from app.modules.banner.models import Banner, BannerPosition
from app.modules.banner.schemas import BannerCreate, BannerUpdate
from app.shared.sort_order import sort_order_service

class BannerService:
    """Nghiệp vụ quản lý Banner."""

    async def list_banners_admin(
        self,
        db: AsyncSession,
        *,
        page: int = 1,
        page_size: int = 10,
        search: Optional[str] = None,
        position: Optional[BannerPosition] = None,
        is_active: Optional[bool] = None,
        sort_by: str = "sort_order",
        order: str = "asc",
    ) -> tuple[list[Banner], int]:
        """
        Lấy danh sách banner phân trang dùng cho trang quản trị Admin.
        """
        skip = (page - 1) * page_size

        # 1. Câu lệnh query chính
        query = select(Banner).where(Banner.deleted_at.is_(None))
        count_query = select(func.count(Banner.id)).where(Banner.deleted_at.is_(None))

        # 2. Áp dụng bộ lọc
        if search:
            search_filter = Banner.title.ilike(f"%{search}%") | Banner.description.ilike(f"%{search}%")
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        if position:
            query = query.where(Banner.position == position)
            count_query = count_query.where(Banner.position == position)

        if is_active is not None:
            query = query.where(Banner.is_active == is_active)
            count_query = count_query.where(Banner.is_active == is_active)

        # 3. Đếm tổng số
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # 4. Sắp xếp động
        sort_attr = getattr(Banner, sort_by, Banner.sort_order)
        if order.lower() == "desc":
            query = query.order_by(sort_attr.desc(), Banner.created_at.desc())
        else:
            query = query.order_by(sort_attr.asc(), Banner.created_at.asc())

        # 5. Phân trang
        query = query.offset(skip).limit(page_size)
        result = await db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def list_banners_portal(
        self,
        db: AsyncSession,
        *,
        position: Optional[BannerPosition] = None,
    ) -> list[Banner]:
        """
        Lấy danh sách banner đang hoạt động và trong thời hạn hiệu lực cho Portal.
        Không phân trang, sắp xếp theo sort_order tăng dần.
        """
        now = datetime.now(UTC)

        query = select(Banner).where(
            Banner.deleted_at.is_(None),
            Banner.is_active.is_(True),
            # Lọc thời gian hiệu lực
            and_(
                Banner.start_at.is_(None) | (Banner.start_at <= now),
                Banner.end_at.is_(None) | (Banner.end_at >= now)
            )
        )

        if position:
            query = query.where(Banner.position == position)

        # Sắp xếp theo sort_order và thời gian tạo
        query = query.order_by(Banner.sort_order.asc(), Banner.created_at.asc())
        
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_banner_by_id(self, db: AsyncSession, banner_id: uuid.UUID) -> Banner:
        """Lấy chi tiết banner theo ID."""
        db_obj = await db.get(Banner, banner_id)
        if not db_obj or db_obj.deleted_at is not None:
            raise NotFoundException(
                message="Không tìm thấy banner",
                error_code="BANNER_NOT_FOUND"
            )
        return db_obj

    async def create_banner(self, db: AsyncSession, payload: BannerCreate) -> Banner:
        """Tạo mới banner và tự động chuẩn hóa sort_order."""
        # Chuẩn bị sort_order
        validated_order = await sort_order_service.prepare_insert(
            db,
            Banner,
            payload.sort_order,
            group_by_field="position",
            group_by_value=payload.position
        )

        db_obj = Banner(
            id=uuid.uuid4(),
            title=payload.title,
            description=payload.description,
            desktop_image_object_key=payload.desktop_image_object_key,
            mobile_image_object_key=payload.mobile_image_object_key,
            link_url=payload.link_url,
            open_in_new_tab=payload.open_in_new_tab,
            position=payload.position,
            sort_order=validated_order,
            start_at=payload.start_at,
            end_at=payload.end_at,
            is_active=payload.is_active
        )
        db.add(db_obj)
        await db.flush()
        return db_obj

    async def update_banner(self, db: AsyncSession, banner_id: uuid.UUID, payload: BannerUpdate) -> Banner:
        """Cập nhật thông tin banner, hỗ trợ đổi vị trí và dịch chuyển sort_order."""
        db_obj = await self.get_banner_by_id(db, banner_id)

        old_position = db_obj.position
        new_position = payload.position or db_obj.position

        # Xử lý sort_order
        if payload.position and payload.position != old_position:
            # Di chuyển sang vị trí hiển thị khác:
            # - Dồn hàng ở vị trí cũ
            await sort_order_service.prepare_delete(
                db, Banner, db_obj.sort_order, group_by_field="position", group_by_value=old_position
            )
            # - Chèn chừa chỗ ở vị trí mới
            target_order = payload.sort_order if payload.sort_order is not None else 999999
            validated_order = await sort_order_service.prepare_insert(
                db, Banner, target_order, group_by_field="position", group_by_value=new_position
            )
            db_obj.position = new_position
            db_obj.sort_order = validated_order
        else:
            # Giữ nguyên vị trí hiển thị, chỉ đổi thứ tự
            if payload.sort_order is not None:
                validated_order = await sort_order_service.prepare_update(
                    db, Banner, banner_id, payload.sort_order, group_by_field="position", group_by_value=old_position
                )
                db_obj.sort_order = validated_order

        # Cập nhật các trường còn lại
        update_data = payload.model_dump(exclude_unset=True)
        if "position" in update_data:
            del update_data["position"]
        if "sort_order" in update_data:
            del update_data["sort_order"]

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        await db.flush()
        return db_obj

    async def update_banner_status(self, db: AsyncSession, banner_id: uuid.UUID, is_active: bool) -> Banner:
        """Bật/tắt trạng thái hoạt động của banner nhanh."""
        db_obj = await self.get_banner_by_id(db, banner_id)
        db_obj.is_active = is_active
        db.add(db_obj)
        await db.flush()
        return db_obj

    async def delete_banner(self, db: AsyncSession, banner_id: uuid.UUID) -> None:
        """Xóa mềm banner và tự động dồn hàng các banner phía sau."""
        db_obj = await self.get_banner_by_id(db, banner_id)

        old_order = db_obj.sort_order
        position = db_obj.position

        # Xóa mềm
        db_obj.deleted_at = datetime.now(UTC)
        db.add(db_obj)
        await db.flush()

        # Dồn hàng vị trí hiển thị tương ứng
        await sort_order_service.prepare_delete(
            db, Banner, old_order, group_by_field="position", group_by_value=position
        )


banner_service = BannerService()
