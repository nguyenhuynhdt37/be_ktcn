import uuid
from typing import TypeVar, Optional, Any
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.models.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)

class SortOrderService:
    """
    Dịch vụ dùng chung để quản lý và tự động cập nhật sort_order liên tục (0-based)
    cho các thực thể trong cơ sở dữ liệu. Đảm bảo tính Transaction và Concurrency.
    """

    @staticmethod
    def _get_filter_query(
        model: type[ModelType],
        group_by_field: Optional[str] = None,
        group_by_value: Optional[Any] = None
    ):
        """Xây dựng query cơ bản lọc theo group_by và deleted_at IS NULL."""
        filters = [model.deleted_at.is_(None)]
        if group_by_field and group_by_value is not None:
            filters.append(getattr(model, group_by_field) == group_by_value)
        return filters

    async def reorder_all(
        self,
        db: AsyncSession,
        model: type[ModelType],
        group_by_field: Optional[str] = None,
        group_by_value: Optional[Any] = None
    ) -> None:
        """
        Chuẩn hóa lại toàn bộ sort_order của các bản ghi đang hoạt động về dạng liên tục từ 0 đến N-1.
        Sử dụng SELECT ... FOR UPDATE để khóa đồng thời và tránh tranh chấp.
        """
        filters = self._get_filter_query(model, group_by_field, group_by_value)
        stmt = (
            select(model)
            .where(and_(*filters))
            .order_by(model.sort_order.asc(), model.created_at.asc())
            .with_for_update()
        )
        res = await db.execute(stmt)
        records = res.scalars().all()

        for idx, record in enumerate(records):
            if record.sort_order != idx:
                record.sort_order = idx
                db.add(record)
        await db.flush()

    async def prepare_insert(
        self,
        db: AsyncSession,
        model: type[ModelType],
        target_order: int,
        group_by_field: Optional[str] = None,
        group_by_value: Optional[Any] = None
    ) -> int:
        """
        Chuẩn bị chèn một bản ghi mới vào vị trí target_order.
        Trả về vị trí sort_order thực tế sau khi áp dụng validation (0 <= target_order <= N).
        Tự động tăng sort_order của các bản ghi >= target_order lên 1.
        """
        # 1. Khóa và lấy toàn bộ bản ghi hiện tại để đếm và chuẩn hóa
        filters = self._get_filter_query(model, group_by_field, group_by_value)
        stmt = (
            select(model)
            .where(and_(*filters))
            .order_by(model.sort_order.asc(), model.created_at.asc())
            .with_for_update()
        )
        res = await db.execute(stmt)
        records = res.scalars().all()
        n = len(records)

        # 2. Validation: min = 0, max = N (tổng số bản ghi hiện tại)
        validated_order = max(0, min(target_order, n))

        # 3. Cập nhật dịch chuyển vị trí cho các bản ghi cũ
        for record in records:
            # Chuẩn hóa thứ tự cũ và dịch chuyển nếu >= validated_order
            current_order = record.sort_order
            new_order = current_order
            if current_order >= validated_order:
                new_order = current_order + 1
            
            # Cập nhật nếu thay đổi
            if record.sort_order != new_order:
                record.sort_order = new_order
                db.add(record)
                
        await db.flush()
        return validated_order

    async def prepare_update(
        self,
        db: AsyncSession,
        model: type[ModelType],
        record_id: uuid.UUID,
        target_order: int,
        group_by_field: Optional[str] = None,
        group_by_value: Optional[Any] = None
    ) -> int:
        """
        Chuẩn bị cập nhật (di chuyển) vị trí của một bản ghi sang target_order.
        Trả về vị trí sort_order thực tế sau khi áp dụng validation (0 <= target_order <= N-1).
        Tự động dịch chuyển các bản ghi khác để giữ thứ tự liên tục.
        """
        # 1. Lấy toàn bộ bản ghi hiện tại để chuẩn hóa và xác định vị trí cũ
        filters = self._get_filter_query(model, group_by_field, group_by_value)
        stmt = (
            select(model)
            .where(and_(*filters))
            .order_by(model.sort_order.asc(), model.created_at.asc())
            .with_for_update()
        )
        res = await db.execute(stmt)
        records = res.scalars().all()
        n = len(records)

        if n == 0:
            return 0

        # 2. Validation: min = 0, max = N - 1
        validated_order = max(0, min(target_order, n - 1))

        # Tìm bản ghi cần cập nhật và vị trí cũ của nó
        target_record = None
        old_order = -1
        for idx, record in enumerate(records):
            # Đồng thời chuẩn hóa lại chỉ số của toàn bộ danh sách để đảm bảo tính liên tục
            record.sort_order = idx
            if record.id == record_id:
                target_record = record
                old_order = idx

        if not target_record:
            return validated_order

        # 3. Dịch chuyển vị trí nếu có sự thay đổi
        if old_order != validated_order:
            if validated_order < old_order:
                # Di chuyển lên trên: tăng các phần tử từ validated_order đến < old_order lên 1
                for record in records:
                    if validated_order <= record.sort_order < old_order:
                        record.sort_order += 1
                        db.add(record)
            else:
                # Di chuyển xuống dưới: giảm các phần tử từ > old_order đến <= validated_order xuống 1
                for record in records:
                    if old_order < record.sort_order <= validated_order:
                        record.sort_order -= 1
                        db.add(record)

            target_record.sort_order = validated_order
            db.add(target_record)

        await db.flush()
        return validated_order

    async def prepare_delete(
        self,
        db: AsyncSession,
        model: type[ModelType],
        deleted_order: int,
        group_by_field: Optional[str] = None,
        group_by_value: Optional[Any] = None
    ) -> None:
        """
        Cập nhật lại thứ tự sau khi xóa một bản ghi ở vị trí deleted_order.
        Giảm sort_order của các bản ghi phía sau (> deleted_order) đi 1.
        """
        filters = self._get_filter_query(model, group_by_field, group_by_value)
        stmt = (
            select(model)
            .where(and_(*filters))
            .order_by(model.sort_order.asc(), model.created_at.asc())
            .with_for_update()
        )
        res = await db.execute(stmt)
        records = res.scalars().all()

        for idx, record in enumerate(records):
            # Chuẩn hóa và dịch chuyển các bản ghi phía sau
            if record.sort_order > deleted_order:
                record.sort_order -= 1
                db.add(record)
            elif record.sort_order != idx and record.sort_order <= deleted_order:
                record.sort_order = idx
                db.add(record)
        await db.flush()

sort_order_service = SortOrderService()
