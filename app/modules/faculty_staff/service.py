import uuid
from datetime import datetime, UTC
from typing import Optional

from sqlalchemy import select, func, and_
from sqlalchemy.orm import joinedload, load_only
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException, ConflictException
from app.modules.faculty_staff.models import Position, Staff, Department
from app.modules.faculty_staff.schemas import (
    PositionCreate,
    PositionUpdate,
    DepartmentCreate,
    DepartmentUpdate,
    StaffCreate,
    StaffUpdate,
)
from app.shared.sort_order import sort_order_service
import re


def slugify(text: str) -> str:
    """
    Chuyển đổi văn bản tiếng Việt có dấu sang không dấu và chuẩn hóa dạng slug.
    """
    text = text.lower()
    text = text.replace('_', '-')
    patterns = {
        '[àáảãạăằắẳẵặâầấẩẫậ]': 'a',
        '[èéẻẽẹêềếểễệ]': 'e',
        '[ìíỉĩị]': 'i',
        '[òóỏõọôồốổỗộơờớởỡợ]': 'o',
        '[ùúủũụưừứửữự]': 'u',
        '[ỳýỷỹỵ]': 'y',
        'đ': 'd'
    }
    for pattern, replacement in patterns.items():
        text = re.sub(pattern, replacement, text)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text)
    return text.strip('-')



class PositionService:
    """Nghiệp vụ quản lý chức vụ công tác của giảng viên."""

    async def list_positions(
        self,
        db: AsyncSession,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        sort_by: str = "sort_order",
        order: str = "asc",
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Position], int]:
        """
        Lấy danh sách chức vụ chưa bị xóa mềm kèm theo số lượng giảng viên giữ chức vụ đó.
        """
        skip = (page - 1) * page_size

        # 1. Câu lệnh select chính
        stmt = (
            select(Position)
            .where(Position.deleted_at.is_(None))
        )
        
        # 2. Câu lệnh count tổng số
        count_stmt = select(func.count(Position.id)).where(Position.deleted_at.is_(None))

        # Lọc tìm kiếm theo tên
        if search:
            search_filter = (Position.name.ilike(f"%{search}%")) | (Position.english_name.ilike(f"%{search}%"))
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)
            
        # Lọc theo trạng thái hoạt động
        if is_active is not None:
            stmt = stmt.where(Position.is_active == is_active)
            count_stmt = count_stmt.where(Position.is_active == is_active)

        # 3. Đếm tổng số
        count_res = await db.execute(count_stmt)
        total = count_res.scalar() or 0

        # 4. Sắp xếp động
        sort_attr = getattr(Position, sort_by, Position.sort_order)
        if order.lower() == "desc":
            stmt = stmt.order_by(sort_attr.desc(), Position.created_at.desc())
        else:
            stmt = stmt.order_by(sort_attr.asc(), Position.created_at.asc())

        # 5. Phân trang
        stmt = stmt.offset(skip).limit(page_size)
        
        result = await db.execute(stmt)
        positions = list(result.scalars().all())

        # 6. Tính staff_count cho từng position bằng truy vấn IN tối ưu hóa
        if positions:
            pos_ids = [p.id for p in positions]
            staff_count_stmt = (
                select(Staff.position_id, func.count(Staff.id))
                .where(Staff.position_id.in_(pos_ids), Staff.deleted_at.is_(None))
                .group_by(Staff.position_id)
            )
            staff_count_res = await db.execute(staff_count_stmt)
            staff_count_map = {row[0]: row[1] for row in staff_count_res.all()}
            for pos in positions:
                pos.staff_count = staff_count_map.get(pos.id, 0)
        else:
            for pos in positions:
                pos.staff_count = 0

        return positions, total

    async def get_position_by_id(self, db: AsyncSession, position_id: uuid.UUID) -> Position:
        """Lấy chi tiết chức vụ theo ID kèm số lượng giảng viên."""
        stmt = (
            select(Position, func.count(Staff.id).label("staff_count"))
            .outerjoin(
                Staff,
                and_(
                    Staff.position_id == Position.id,
                    Staff.deleted_at.is_(None)
                )
            )
            .where(Position.id == position_id, Position.deleted_at.is_(None))
            .group_by(Position.id)
        )
        result = await db.execute(stmt)
        row = result.first()
        if not row:
            raise NotFoundException(
                message="Không tìm thấy chức vụ",
                error_code="POSITION_NOT_FOUND"
            )
        pos, staff_count = row
        pos.staff_count = staff_count
        return pos

    async def create_position(self, db: AsyncSession, payload: PositionCreate) -> Position:
        """Tạo chức vụ mới, chặn trùng tên đối với các bản ghi đang hoạt động."""
        # Kiểm tra trùng tên trong các chức vụ chưa bị xóa mềm
        stmt = select(Position).where(
            Position.name == payload.name,
            Position.deleted_at.is_(None)
        )
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            raise ConflictException(
                message="Tên chức vụ đã tồn tại trong hệ thống",
                error_code="DUPLICATE_POSITION_NAME"
            )

        validated_order = await sort_order_service.prepare_insert(db, Position, payload.sort_order)

        db_obj = Position(
            name=payload.name,
            english_name=payload.english_name,
            description=payload.description,
            sort_order=validated_order,
            is_active=payload.is_active
        )
        db.add(db_obj)
        await db.flush()
        
        db_obj.staff_count = 0
        return db_obj

    async def update_position(
        self, db: AsyncSession, position_id: uuid.UUID, payload: PositionUpdate
    ) -> Position:
        """Cập nhật thông tin chi tiết chức vụ, kiểm tra trùng tên khi đổi tên."""
        db_obj = await db.get(Position, position_id)
        if not db_obj or db_obj.deleted_at is not None:
            raise NotFoundException(
                message="Không tìm thấy chức vụ để cập nhật",
                error_code="POSITION_NOT_FOUND"
            )

        # Kiểm tra trùng tên với chức vụ đang hoạt động khác
        if payload.name and payload.name != db_obj.name:
            stmt = select(Position).where(
                Position.name == payload.name,
                Position.deleted_at.is_(None),
                Position.id != position_id
            )
            res = await db.execute(stmt)
            if res.scalar_one_or_none():
                raise ConflictException(
                    message="Tên chức vụ đã tồn tại trong hệ thống",
                    error_code="DUPLICATE_POSITION_NAME"
                )

        if payload.sort_order is not None:
            validated_order = await sort_order_service.prepare_update(db, Position, position_id, payload.sort_order)
            db_obj.sort_order = validated_order

        update_data = payload.model_dump(exclude_unset=True)
        if "sort_order" in update_data:
            del update_data["sort_order"]

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        await db.flush()

        # Tính toán lại staff_count
        count_stmt = select(func.count(Staff.id)).where(
            Staff.position_id == position_id,
            Staff.deleted_at.is_(None)
        )
        count_res = await db.execute(count_stmt)
        db_obj.staff_count = count_res.scalar_one()

        return db_obj

    async def update_position_status(
        self, db: AsyncSession, position_id: uuid.UUID, is_active: bool
    ) -> Position:
        """Bật/tắt trạng thái hoạt động của chức vụ."""
        db_obj = await db.get(Position, position_id)
        if not db_obj or db_obj.deleted_at is not None:
            raise NotFoundException(
                message="Không tìm thấy chức vụ",
                error_code="POSITION_NOT_FOUND"
            )

        db_obj.is_active = is_active
        db.add(db_obj)
        await db.flush()

        # Tính toán lại staff_count
        count_stmt = select(func.count(Staff.id)).where(
            Staff.position_id == position_id,
            Staff.deleted_at.is_(None)
        )
        count_res = await db.execute(count_stmt)
        db_obj.staff_count = count_res.scalar_one()

        return db_obj

    async def delete_position(self, db: AsyncSession, position_id: uuid.UUID) -> None:
        """Xóa mềm chức vụ, chặn xóa nếu đang có giảng viên hoạt động liên kết."""
        db_obj = await db.get(Position, position_id)
        if not db_obj or db_obj.deleted_at is not None:
            raise NotFoundException(
                message="Không tìm thấy chức vụ để xóa",
                error_code="POSITION_NOT_FOUND"
            )

        # Kiểm tra xem có giảng viên hoạt động nào liên kết với chức vụ này không
        count_stmt = select(func.count(Staff.id)).where(
            Staff.position_id == position_id,
            Staff.deleted_at.is_(None)
        )
        count_res = await db.execute(count_stmt)
        staff_count = count_res.scalar_one()

        if staff_count > 0:
            raise BadRequestException(
                message=f"Không thể xóa chức vụ này vì hiện có {staff_count} giảng viên đang giữ chức vụ",
                error_code="CANNOT_DELETE_ACTIVE_POSITION"
            )

        # Lưu lại sort_order cũ trước khi xóa mềm
        old_order = db_obj.sort_order

        # Tiến hành xóa mềm bằng cách cập nhật deleted_at
        db_obj.deleted_at = datetime.now(UTC)
        db.add(db_obj)
        await db.flush()

        # Dồn hàng và cập nhật lại sort_order cho các vị trí còn lại
        await sort_order_service.prepare_delete(db, Position, old_order)

    async def get_stats(self, db: AsyncSession) -> dict:
        """Lấy số liệu thống kê tổng quan về các chức vụ."""
        total_stmt = select(func.count(Position.id)).where(Position.deleted_at.is_(None))
        active_stmt = select(func.count(Position.id)).where(Position.deleted_at.is_(None), Position.is_active.is_(True))
        inactive_stmt = select(func.count(Position.id)).where(Position.deleted_at.is_(None), Position.is_active.is_(False))
        
        staff_count_stmt = select(func.count(Staff.id)).where(
            Staff.deleted_at.is_(None),
            Staff.is_active.is_(True),
            Staff.position_id.isnot(None)
        )

        total_res = await db.execute(total_stmt)
        active_res = await db.execute(active_stmt)
        inactive_res = await db.execute(inactive_stmt)
        staff_res = await db.execute(staff_count_stmt)

        return {
            "total": total_res.scalar() or 0,
            "active": active_res.scalar() or 0,
            "inactive": inactive_res.scalar() or 0,
            "total_staff": staff_res.scalar() or 0
        }


position_service = PositionService()


class DepartmentService:
    """Nghiệp vụ quản lý bộ môn/khoa của trường."""

    async def list_departments(
        self,
        db: AsyncSession,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        sort_by: str = "sort_order",
        order: str = "asc",
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Department], int]:
        """
        Lấy danh sách bộ môn kèm theo số lượng giảng viên thuộc bộ môn đó.
        """
        skip = (page - 1) * page_size

        # 1. Câu lệnh select chính
        stmt = (
            select(Department)
            .where(Department.deleted_at.is_(None))
        )
        
        # 2. Câu lệnh count tổng số
        count_stmt = select(func.count(Department.id)).where(Department.deleted_at.is_(None))

        # Lọc tìm kiếm theo tên
        if search:
            search_filter = (Department.name.ilike(f"%{search}%")) | (Department.english_name.ilike(f"%{search}%"))
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)

        # Lọc theo trạng thái hoạt động
        if is_active is not None:
            stmt = stmt.where(Department.is_active == is_active)
            count_stmt = count_stmt.where(Department.is_active == is_active)

        # 3. Đếm tổng số
        count_res = await db.execute(count_stmt)
        total = count_res.scalar() or 0

        # 4. Sắp xếp động
        sort_attr = getattr(Department, sort_by, Department.sort_order)
        if order.lower() == "desc":
            stmt = stmt.order_by(sort_attr.desc(), Department.created_at.desc())
        else:
            stmt = stmt.order_by(sort_attr.asc(), Department.created_at.asc())

        # 5. Phân trang
        stmt = stmt.offset(skip).limit(page_size)
        
        result = await db.execute(stmt)
        departments = list(result.scalars().all())

        # 6. Tính staff_count cho từng department bằng truy vấn IN tối ưu hóa
        if departments:
            dept_ids = [d.id for d in departments]
            staff_count_stmt = (
                select(Staff.department_id, func.count(Staff.id))
                .where(Staff.department_id.in_(dept_ids), Staff.deleted_at.is_(None))
                .group_by(Staff.department_id)
            )
            staff_count_res = await db.execute(staff_count_stmt)
            staff_count_map = {row[0]: row[1] for row in staff_count_res.all()}
            for dept in departments:
                dept.staff_count = staff_count_map.get(dept.id, 0)
        else:
            for dept in departments:
                dept.staff_count = 0

        return departments, total

    async def get_department_by_id(self, db: AsyncSession, department_id: uuid.UUID) -> Department:
        """Lấy chi tiết bộ môn theo ID."""
        stmt = (
            select(Department, func.count(Staff.id).label("staff_count"))
            .outerjoin(
                Staff,
                and_(
                    Staff.department_id == Department.id,
                    Staff.deleted_at.is_(None)
                )
            )
            .where(Department.id == department_id, Department.deleted_at.is_(None))
            .group_by(Department.id)
        )
        result = await db.execute(stmt)
        row = result.first()
        if not row:
            raise NotFoundException(
                message="Không tìm thấy bộ môn",
                error_code="DEPARTMENT_NOT_FOUND"
            )
        dept, staff_count = row
        dept.staff_count = staff_count
        return dept

    async def create_department(self, db: AsyncSession, payload: DepartmentCreate) -> Department:
        """Tạo bộ môn mới, tự động sinh slug và kiểm tra trùng tên/slug."""
        # Kiểm tra trùng tên hoạt động
        stmt_name = select(Department).where(
            Department.name == payload.name,
            Department.deleted_at.is_(None)
        )
        res_name = await db.execute(stmt_name)
        if res_name.scalar_one_or_none():
            raise ConflictException(
                message="Tên bộ môn đã tồn tại trong hệ thống",
                error_code="DUPLICATE_DEPARTMENT_NAME"
            )

        # Tạo slug và kiểm tra trùng slug hoạt động
        slug = slugify(payload.name)
        stmt_slug = select(Department).where(
            Department.slug == slug,
            Department.deleted_at.is_(None)
        )
        res_slug = await db.execute(stmt_slug)
        if res_slug.scalar_one_or_none():
            base_slug = slug
            counter = 1
            while True:
                slug = f"{base_slug}-{counter}"
                stmt_check = select(Department).where(
                    Department.slug == slug,
                    Department.deleted_at.is_(None)
                )
                res_check = await db.execute(stmt_check)
                if not res_check.scalar_one_or_none():
                    break
                counter += 1

        validated_order = await sort_order_service.prepare_insert(db, Department, payload.sort_order)

        db_obj = Department(
            name=payload.name,
            english_name=payload.english_name,
            slug=slug,
            description=payload.description,
            thumbnail_object_key=payload.thumbnail_object_key,
            phone=payload.phone,
            email=payload.email,
            website=payload.website,
            office=payload.office,
            sort_order=validated_order,
            is_active=payload.is_active
        )
        db.add(db_obj)
        await db.flush()
        db_obj.staff_count = 0
        return db_obj

    async def update_department(
        self, db: AsyncSession, department_id: uuid.UUID, payload: DepartmentUpdate
    ) -> Department:
        """Cập nhật thông tin chi tiết bộ môn, cập nhật lại slug nếu đổi tên."""
        db_obj = await db.get(Department, department_id)
        if not db_obj or db_obj.deleted_at is not None:
            raise NotFoundException(
                message="Không tìm thấy bộ môn để cập nhật",
                error_code="DEPARTMENT_NOT_FOUND"
            )

        # Kiểm tra trùng tên
        if payload.name and payload.name != db_obj.name:
            stmt_name = select(Department).where(
                Department.name == payload.name,
                Department.deleted_at.is_(None),
                Department.id != department_id
            )
            res_name = await db.execute(stmt_name)
            if res_name.scalar_one_or_none():
                raise ConflictException(
                    message="Tên bộ môn đã tồn tại trong hệ thống",
                    error_code="DUPLICATE_DEPARTMENT_NAME"
                )

            # Cập nhật slug mới
            slug = slugify(payload.name)
            stmt_slug = select(Department).where(
                Department.slug == slug,
                Department.deleted_at.is_(None),
                Department.id != department_id
            )
            res_slug = await db.execute(stmt_slug)
            if res_slug.scalar_one_or_none():
                base_slug = slug
                counter = 1
                while True:
                    slug = f"{base_slug}-{counter}"
                    stmt_check = select(Department).where(
                        Department.slug == slug,
                        Department.deleted_at.is_(None),
                        Department.id != department_id
                    )
                    res_check = await db.execute(stmt_check)
                    if not res_check.scalar_one_or_none():
                        break
                    counter += 1
            db_obj.slug = slug

        if payload.sort_order is not None:
            validated_order = await sort_order_service.prepare_update(db, Department, department_id, payload.sort_order)
            db_obj.sort_order = validated_order

        update_data = payload.model_dump(exclude_unset=True)
        if "sort_order" in update_data:
            del update_data["sort_order"]

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        await db.flush()

        # Tính toán lại staff_count
        count_stmt = select(func.count(Staff.id)).where(
            Staff.department_id == department_id,
            Staff.deleted_at.is_(None)
        )
        count_res = await db.execute(count_stmt)
        db_obj.staff_count = count_res.scalar_one()

        return db_obj

    async def update_department_status(
        self, db: AsyncSession, department_id: uuid.UUID, is_active: bool
    ) -> Department:
        """Bật/tắt trạng thái hoạt động của bộ môn."""
        db_obj = await db.get(Department, department_id)
        if not db_obj or db_obj.deleted_at is not None:
            raise NotFoundException(
                message="Không tìm thấy bộ môn",
                error_code="DEPARTMENT_NOT_FOUND"
            )

        db_obj.is_active = is_active
        db.add(db_obj)
        await db.flush()

        # Tính toán lại staff_count
        count_stmt = select(func.count(Staff.id)).where(
            Staff.department_id == department_id,
            Staff.deleted_at.is_(None)
        )
        count_res = await db.execute(count_stmt)
        db_obj.staff_count = count_res.scalar_one()

        return db_obj

    async def delete_department(self, db: AsyncSession, department_id: uuid.UUID) -> None:
        """Xóa mềm bộ môn, chặn xóa nếu đang có giảng viên hoạt động liên kết."""
        db_obj = await db.get(Department, department_id)
        if not db_obj or db_obj.deleted_at is not None:
            raise NotFoundException(
                message="Không tìm thấy bộ môn để xóa",
                error_code="DEPARTMENT_NOT_FOUND"
            )

        # Kiểm tra xem có giảng viên hoạt động nào liên kết với bộ môn này không
        count_stmt = select(func.count(Staff.id)).where(
            Staff.department_id == department_id,
            Staff.deleted_at.is_(None)
        )
        count_res = await db.execute(count_stmt)
        staff_count = count_res.scalar_one()

        if staff_count > 0:
            raise BadRequestException(
                message=f"Không thể xóa bộ môn này vì hiện có {staff_count} giảng viên đang thuộc bộ môn",
                error_code="CANNOT_DELETE_ACTIVE_DEPARTMENT"
            )

        # Lưu lại sort_order cũ trước khi xóa mềm
        old_order = db_obj.sort_order

        # Xóa mềm
        db_obj.deleted_at = datetime.now(UTC)
        db.add(db_obj)
        await db.flush()

        # Dồn hàng và cập nhật lại sort_order cho các bộ môn còn lại
        await sort_order_service.prepare_delete(db, Department, old_order)

    async def get_stats(self, db: AsyncSession) -> dict:
        """Lấy số liệu thống kê tổng quan về các bộ môn."""
        total_stmt = select(func.count(Department.id)).where(Department.deleted_at.is_(None))
        active_stmt = select(func.count(Department.id)).where(Department.deleted_at.is_(None), Department.is_active.is_(True))
        inactive_stmt = select(func.count(Department.id)).where(Department.deleted_at.is_(None), Department.is_active.is_(False))
        
        staff_count_stmt = select(func.count(Staff.id)).where(
            Staff.deleted_at.is_(None),
            Staff.is_active.is_(True),
            Staff.department_id.isnot(None)
        )

        total_res = await db.execute(total_stmt)
        active_res = await db.execute(active_stmt)
        inactive_res = await db.execute(inactive_stmt)
        staff_res = await db.execute(staff_count_stmt)

        return {
            "total": total_res.scalar() or 0,
            "active": active_res.scalar() or 0,
            "inactive": inactive_res.scalar() or 0,
            "total_staff": staff_res.scalar() or 0
        }


department_service = DepartmentService()


class StaffService:
    """Nghiệp vụ quản lý hồ sơ giảng viên/cán bộ."""

    async def list_staffs(
        self,
        db: AsyncSession,
        *,
        page: int = 1,
        page_size: int = 10,
        search: Optional[str] = None,
        department_id: Optional[uuid.UUID] = None,
        position_id: Optional[uuid.UUID] = None,
        academic_title: Optional[str] = None,
        degree: Optional[str] = None,
        is_active: Optional[bool] = None,
        sort_by: str = "sort_order",
        order: str = "asc",
    ) -> tuple[list[Staff], int]:
        """
        Lấy danh sách giảng viên phân trang, lọc nâng cao và eager load thông tin Department, Position.
        """
        skip = (page - 1) * page_size

        # 1. Khởi tạo Query Builder
        query = select(Staff).outerjoin(Department, Staff.department_id == Department.id).where(Staff.deleted_at.is_(None))
        count_query = select(func.count(Staff.id)).where(Staff.deleted_at.is_(None))

        # 2. Áp dụng các bộ lọc
        if search:
            search_filter = Staff.full_name.ilike(f"%{search}%") | Staff.english_name.ilike(f"%{search}%")
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        if department_id:
            query = query.where(Staff.department_id == department_id)
            count_query = count_query.where(Staff.department_id == department_id)

        if position_id:
            query = query.where(Staff.position_id == position_id)
            count_query = count_query.where(Staff.position_id == position_id)

        if academic_title:
            query = query.where(Staff.academic_title == academic_title)
            count_query = count_query.where(Staff.academic_title == academic_title)

        if degree:
            query = query.where(Staff.degree == degree)
            count_query = count_query.where(Staff.degree == degree)

        if is_active is not None:
            query = query.where(Staff.is_active == is_active)
            count_query = count_query.where(Staff.is_active == is_active)

        # 3. Đếm tổng số bản ghi
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # 4. Eager Loading & Load Only để tối ưu hóa
        query = query.options(
            joinedload(Staff.department).load_only(
                Department.id, Department.name, Department.slug, Department.is_active
            ),
            joinedload(Staff.position).load_only(
                Position.id, Position.name, Position.sort_order, Position.is_active
            ),
            load_only(
                Staff.id,
                Staff.department_id,
                Staff.position_id,
                Staff.full_name,
                Staff.english_name,
                Staff.slug,
                Staff.academic_title,
                Staff.degree,
                Staff.avatar_object_key,
                Staff.email,
                Staff.phone,
                Staff.website,
                Staff.office,
                Staff.biography,
                Staff.research_interests,
                Staff.sort_order,
                Staff.is_active,
                Staff.created_at,
                Staff.updated_at,
            )
        )

        # 5. Sắp xếp động
        if sort_by == "sort_order":
            if order.lower() == "desc":
                query = query.order_by(Department.sort_order.desc(), Staff.sort_order.desc(), Staff.created_at.desc())
            else:
                query = query.order_by(Department.sort_order.asc(), Staff.sort_order.asc(), Staff.created_at.asc())
        else:
            sort_attr = getattr(Staff, sort_by, Staff.sort_order)
            if order.lower() == "desc":
                query = query.order_by(sort_attr.desc(), Staff.created_at.desc())
            else:
                query = query.order_by(sort_attr.asc(), Staff.created_at.asc())

        # 6. Phân trang
        query = query.offset(skip).limit(page_size)

        result = await db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_staff_by_id(self, db: AsyncSession, staff_id: uuid.UUID) -> Staff:
        """Lấy chi tiết giảng viên theo ID kèm eager load."""
        stmt = (
            select(Staff)
            .options(
                joinedload(Staff.department).load_only(
                    Department.id, Department.name, Department.slug, Department.is_active
                ),
                joinedload(Staff.position).load_only(
                    Position.id, Position.name, Position.sort_order, Position.is_active
                ),
            )
            .where(Staff.id == staff_id, Staff.deleted_at.is_(None))
        )
        result = await db.execute(stmt)
        obj = result.scalar_one_or_none()
        if not obj:
            raise NotFoundException(
                message="Không tìm thấy giảng viên",
                error_code="STAFF_NOT_FOUND"
            )
        return obj

    async def get_staff_by_slug(self, db: AsyncSession, slug: str) -> Staff:
        """Lấy chi tiết giảng viên theo Slug (phục vụ SEO)."""
        stmt = (
            select(Staff)
            .options(
                joinedload(Staff.department).load_only(
                    Department.id, Department.name, Department.slug, Department.is_active
                ),
                joinedload(Staff.position).load_only(
                    Position.id, Position.name, Position.sort_order, Position.is_active
                ),
            )
            .where(Staff.slug == slug, Staff.deleted_at.is_(None))
        )
        result = await db.execute(stmt)
        obj = result.scalar_one_or_none()
        if not obj:
            raise NotFoundException(
                message="Không tìm thấy giảng viên với slug cung cấp",
                error_code="STAFF_NOT_FOUND"
            )
        return obj

    async def _generate_unique_slug(self, db: AsyncSession, name: str, exclude_id: Optional[uuid.UUID] = None) -> str:
        """Sinh slug độc nhất cho giảng viên."""
        base_slug = slugify(name)
        slug = base_slug
        counter = 1
        while True:
            stmt = select(Staff).where(Staff.slug == slug, Staff.deleted_at.is_(None))
            if exclude_id:
                stmt = stmt.where(Staff.id != exclude_id)
            res = await db.execute(stmt)
            if not res.scalar_one_or_none():
                break
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

    async def _validate_foreign_keys(self, db: AsyncSession, department_id: uuid.UUID, position_id: uuid.UUID) -> None:
        """Kiểm tra sự tồn tại của bộ môn và chức vụ."""
        dept = await db.get(Department, department_id)
        if not dept or dept.deleted_at is not None:
            raise NotFoundException(
                message="Bộ môn được liên kết không tồn tại trong hệ thống",
                error_code="DEPARTMENT_NOT_FOUND"
            )
        pos = await db.get(Position, position_id)
        if not pos or pos.deleted_at is not None:
            raise NotFoundException(
                message="Chức vụ được liên kết không tồn tại trong hệ thống",
                error_code="POSITION_NOT_FOUND"
            )

    async def create_staff(self, db: AsyncSession, payload: StaffCreate) -> Staff:
        """Tạo hồ sơ giảng viên mới, tự sinh slug độc nhất và xác thực FK."""
        # 1. Xác thực Foreign Keys trước khi chèn
        await self._validate_foreign_keys(db, payload.department_id, payload.position_id)

        # 2. Chuẩn bị sort_order trong cùng bộ môn
        validated_order = await sort_order_service.prepare_insert(
            db, Staff, payload.sort_order, group_by_field="department_id", group_by_value=payload.department_id
        )

        # 3. Sinh slug độc nhất
        slug = await self._generate_unique_slug(db, payload.full_name)

        # 4. Tạo model object
        db_obj = Staff(
            department_id=payload.department_id,
            position_id=payload.position_id,
            full_name=payload.full_name,
            english_name=payload.english_name,
            slug=slug,
            academic_title=payload.academic_title,
            degree=payload.degree,
            avatar_object_key=payload.avatar_object_key,
            email=payload.email,
            phone=payload.phone,
            website=payload.website,
            office=payload.office,
            biography=payload.biography,
            research_interests=payload.research_interests,
            sort_order=validated_order,
            is_active=payload.is_active
        )
        db.add(db_obj)
        await db.flush()
        
        # Load các liên kết để trả về schema response chuẩn
        return await self.get_staff_by_id(db, db_obj.id)

    async def update_staff(
        self, db: AsyncSession, staff_id: uuid.UUID, payload: StaffUpdate
    ) -> Staff:
        """Cập nhật hồ sơ giảng viên, cập nhật lại slug nếu đổi tên."""
        db_obj = await db.get(Staff, staff_id)
        if not db_obj or db_obj.deleted_at is not None:
            raise NotFoundException(
                message="Không tìm thấy giảng viên để cập nhật",
                error_code="STAFF_NOT_FOUND"
            )

        # 1. Xác thực FK nếu có thay đổi
        old_dept_id = db_obj.department_id
        new_dept_id = payload.department_id or db_obj.department_id
        pos_id = payload.position_id or db_obj.position_id
        if payload.department_id or payload.position_id:
            await self._validate_foreign_keys(db, new_dept_id, pos_id)

        # 2. Cập nhật thứ tự hiển thị dựa theo việc đổi bộ môn hay đổi vị trí trong bộ môn
        if payload.department_id and payload.department_id != old_dept_id:
            # Di chuyển sang bộ môn khác:
            # - Dồn hàng bộ môn cũ
            await sort_order_service.prepare_delete(
                db, Staff, db_obj.sort_order, group_by_field="department_id", group_by_value=old_dept_id
            )
            # - Chèn vào bộ môn mới
            target_order = payload.sort_order if payload.sort_order is not None else 999999
            validated_order = await sort_order_service.prepare_insert(
                db, Staff, target_order, group_by_field="department_id", group_by_value=new_dept_id
            )
            db_obj.department_id = new_dept_id
            db_obj.sort_order = validated_order
        else:
            # Giữ nguyên bộ môn, chỉ thay đổi thứ tự nếu được truyền
            if payload.sort_order is not None:
                validated_order = await sort_order_service.prepare_update(
                    db, Staff, staff_id, payload.sort_order, group_by_field="department_id", group_by_value=old_dept_id
                )
                db_obj.sort_order = validated_order

        # 3. Cập nhật slug nếu đổi tên
        if payload.full_name and payload.full_name != db_obj.full_name:
            db_obj.slug = await self._generate_unique_slug(db, payload.full_name, exclude_id=staff_id)

        # 4. Cập nhật các trường còn lại (bỏ qua department_id và sort_order đã được xử lý thủ công)
        update_data = payload.model_dump(exclude_unset=True)
        if "department_id" in update_data:
            del update_data["department_id"]
        if "sort_order" in update_data:
            del update_data["sort_order"]

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        await db.flush()

        return await self.get_staff_by_id(db, staff_id)

    async def update_staff_status(
        self, db: AsyncSession, staff_id: uuid.UUID, is_active: bool
    ) -> Staff:
        """Cập nhật nhanh trạng thái hoạt động của giảng viên."""
        db_obj = await db.get(Staff, staff_id)
        if not db_obj or db_obj.deleted_at is not None:
            raise NotFoundException(
                message="Không tìm thấy giảng viên",
                error_code="STAFF_NOT_FOUND"
            )

        db_obj.is_active = is_active
        db.add(db_obj)
        await db.flush()

        return await self.get_staff_by_id(db, staff_id)

    async def delete_staff(self, db: AsyncSession, staff_id: uuid.UUID) -> None:
        """Xóa mềm giảng viên."""
        db_obj = await db.get(Staff, staff_id)
        if not db_obj or db_obj.deleted_at is not None:
            raise NotFoundException(
                message="Không tìm thấy giảng viên để xóa",
                error_code="STAFF_NOT_FOUND"
            )

        old_order = db_obj.sort_order
        dept_id = db_obj.department_id

        db_obj.deleted_at = datetime.now(UTC)
        db.add(db_obj)
        await db.flush()

        await sort_order_service.prepare_delete(
            db, Staff, old_order, group_by_field="department_id", group_by_value=dept_id
        )

    async def get_stats(self, db: AsyncSession) -> dict:
        """Lấy số liệu thống kê tổng quan về đội ngũ giảng viên và trình độ chuyên môn."""
        total_stmt = select(func.count(Staff.id)).where(Staff.deleted_at.is_(None))
        active_stmt = select(func.count(Staff.id)).where(Staff.deleted_at.is_(None), Staff.is_active.is_(True))
        inactive_stmt = select(func.count(Staff.id)).where(Staff.deleted_at.is_(None), Staff.is_active.is_(False))
        
        # Đếm giảng viên trình độ cao: Giáo sư, Phó Giáo sư hoặc Tiến sĩ
        high_qual_stmt = select(func.count(Staff.id)).where(
            Staff.deleted_at.is_(None),
            (Staff.academic_title.in_(["Giáo sư", "Phó Giáo sư"])) | (Staff.degree == "Tiến sĩ")
        )

        total_res = await db.execute(total_stmt)
        active_res = await db.execute(active_stmt)
        inactive_res = await db.execute(inactive_stmt)
        high_qual_res = await db.execute(high_qual_stmt)

        return {
            "total": total_res.scalar() or 0,
            "active": active_res.scalar() or 0,
            "inactive": inactive_res.scalar() or 0,
            "high_qualification": high_qual_res.scalar() or 0
        }


staff_service = StaffService()


