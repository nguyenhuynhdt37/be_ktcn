import re
import uuid
from datetime import UTC, datetime
from typing import Optional, Tuple
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.exceptions import BadRequestException, NotFoundException
from app.modules.staff.models import Staff, StaffTranslation
from app.modules.staff.schemas import StaffCreate, StaffUpdate
from app.modules.language.models import Language
from app.modules.department.models import Department
from app.modules.position.models import Position
from app.modules.academic_title.models import AcademicTitle
from app.modules.degree.models import Degree


class StaffService:
    def slugify(self, text: str) -> str:
        unicode_map = {
            'a': 'áàảãạăắằẳẵặâấầẩẫậ',
            'd': 'đ',
            'e': 'éèẻẽẹêếềểễệ',
            'i': 'íìỉĩị',
            'o': 'óòỏõọôốồổỗộơớờởỡợ',
            'u': 'úùủũụưứừửữự',
            'y': 'ýỳỷỹỵ',
            'A': 'ÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬ',
            'D': 'Đ',
            'E': 'ÉÈẺẼẸÊẾỀỂỄỆ',
            'I': 'ÍÌÌỈĨỊ',
            'O': 'ÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢ',
            'U': 'ÚÙỦŨỤƯỨỪỬỮỰ',
            'Y': 'ÝỲỶỸỴ'
        }
        text = text.strip()
        for english, vietnamese in unicode_map.items():
            for char in vietnamese:
                text = text.replace(char, english)
        text = text.lower()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[\s_-]+', '-', text)
        return text

    async def get_language_map(self, db: AsyncSession) -> dict[str, uuid.UUID]:
        stmt = select(Language).where(Language.is_active == True)
        result = await db.execute(stmt)
        return {lang.code: lang.id for lang in result.scalars().all()}

    def _apply_translation(self, staff: Staff, lang: str = "vi") -> Staff:
        """Gán các thuộc tính động (academic_title, degree, biography, research_interests) dựa trên ngôn ngữ."""
        matched = None
        for t in staff.translations:
            if t.language.code == lang:
                matched = t
                break
        if not matched and lang != "vi":
            for t in staff.translations:
                if t.language.code == "vi":
                    matched = t
                    break
        if not matched and staff.translations:
            matched = staff.translations[0]

        # Dịch động AcademicTitle
        academic_title_resolved = None
        if staff.academic_title:
            t_matched = None
            for t in staff.academic_title.translations:
                if t.language.code == lang:
                    t_matched = t
                    break
            if not t_matched:
                for t in staff.academic_title.translations:
                    if t.language.is_default:
                        t_matched = t
                        break
            if t_matched:
                academic_title_resolved = t_matched.name
        staff.academic_title_resolved = academic_title_resolved

        # Dịch động Degree
        degree_resolved = None
        if staff.degree:
            d_matched = None
            for d in staff.degree.translations:
                if d.language.code == lang:
                    d_matched = d
                    break
            if not d_matched:
                for d in staff.degree.translations:
                    if d.language.is_default:
                        d_matched = d
                        break
            if d_matched:
                degree_resolved = d_matched.name
        staff.degree_resolved = degree_resolved
        staff.biography = matched.biography if matched else None
        staff.research_interests = matched.research_interests if matched else None

        # Resolve relation translation if loaded
        if staff.department:
            dept_matched = None
            for dt in staff.department.translations:
                if dt.language.code == lang:
                    dept_matched = dt
                    break
            if not dept_matched and lang != "vi":
                for dt in staff.department.translations:
                    if dt.language.code == "vi":
                        dept_matched = dt
                        break
            staff.department.name = dept_matched.name if dept_matched else ""
            staff.department.slug = dept_matched.slug if dept_matched else ""
            staff.department.description = dept_matched.description if dept_matched else None

        if staff.position:
            pos_matched = None
            for pt in staff.position.translations:
                if pt.language.code == lang:
                    pos_matched = pt
                    break
            if not pos_matched and lang != "vi":
                for pt in staff.position.translations:
                    if pt.language.code == "vi":
                        pos_matched = pt
                        break
            staff.position.name = pos_matched.name if pos_matched else ""
            staff.position.description = pos_matched.description if pos_matched else None

        return staff

    async def list_staffs(
        self,
        db: AsyncSession,
        search: Optional[str] = None,
        department_id: Optional[uuid.UUID] = None,
        position_id: Optional[uuid.UUID] = None,
        academic_title_id: Optional[uuid.UUID] = None,
        degree_id: Optional[uuid.UUID] = None,
        is_active: Optional[bool] = None,
        sort_by: str = "sort_order",
        order: str = "asc",
        page: int = 1,
        page_size: int = 10,
        lang: str = "vi",
    ) -> Tuple[list[Staff], int]:
        stmt = (
            select(Staff)
            .where(Staff.deleted_at.is_(None))
            .options(
                selectinload(Staff.department).selectinload(Department.translations),
                selectinload(Staff.position).selectinload(Position.translations),
                selectinload(Staff.academic_title).selectinload(AcademicTitle.translations),
                selectinload(Staff.degree).selectinload(Degree.translations)
            )
        )

        if is_active is not None:
            stmt = stmt.where(Staff.is_active == is_active)
        if department_id is not None:
            stmt = stmt.where(Staff.department_id == department_id)
        if position_id is not None:
            stmt = stmt.where(Staff.position_id == position_id)
        if academic_title_id is not None:
            stmt = stmt.where(Staff.academic_title_id == academic_title_id)
        if degree_id is not None:
            stmt = stmt.where(Staff.degree_id == degree_id)

        if search:
            stmt = stmt.join(StaffTranslation, isouter=True).where(
                or_(
                    Staff.full_name.ilike(f"%{search}%"),
                    Staff.english_name.ilike(f"%{search}%"),
                    StaffTranslation.biography.ilike(f"%{search}%"),
                    StaffTranslation.research_interests.ilike(f"%{search}%"),
                )
            ).distinct()

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await db.execute(count_stmt)
        total_count = total.scalar() or 0

        # Sort & Pagination
        if sort_by == "sort_order":
            stmt = stmt.join(Department, Staff.department_id == Department.id, isouter=True)
            if order == "desc":
                stmt = stmt.order_by(Department.sort_order.desc(), Staff.sort_order.desc(), Staff.created_at.desc())
            else:
                stmt = stmt.order_by(Department.sort_order.asc(), Staff.sort_order.asc(), Staff.created_at.desc())
        else:
            sort_attr = getattr(Staff, sort_by, Staff.sort_order)
            if order == "desc":
                stmt = stmt.order_by(sort_attr.desc())
            else:
                stmt = stmt.order_by(sort_attr.asc())

        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        result = await db.execute(stmt)
        staffs = result.scalars().all()

        for s in staffs:
            self._apply_translation(s, lang=lang)

        return list(staffs), total_count

    async def get_staff(self, db: AsyncSession, staff_id: uuid.UUID, lang: str = "vi") -> Staff:
        stmt = (
            select(Staff)
            .where(Staff.id == staff_id, Staff.deleted_at.is_(None))
            .options(
                selectinload(Staff.department).selectinload(Department.translations),
                selectinload(Staff.position).selectinload(Position.translations),
                selectinload(Staff.academic_title).selectinload(AcademicTitle.translations),
                selectinload(Staff.degree).selectinload(Degree.translations)
            )
        )
        result = await db.execute(stmt)
        staff = result.scalar_one_or_none()
        if not staff:
            raise NotFoundException("Không tìm thấy giảng viên")
        self._apply_translation(staff, lang=lang)
        return staff

    async def get_staff_by_slug(self, db: AsyncSession, slug: str, lang: str = "vi") -> Staff:
        stmt = (
            select(Staff)
            .where(Staff.slug == slug, Staff.deleted_at.is_(None))
            .options(
                selectinload(Staff.department).selectinload(Department.translations),
                selectinload(Staff.position).selectinload(Position.translations),
                selectinload(Staff.academic_title).selectinload(AcademicTitle.translations),
                selectinload(Staff.degree).selectinload(Degree.translations)
            )
        )
        result = await db.execute(stmt)
        staff = result.scalar_one_or_none()
        if not staff:
            raise NotFoundException("Không tìm thấy giảng viên")
        self._apply_translation(staff, lang=lang)
        return staff

    async def create_staff(self, db: AsyncSession, data: StaffCreate) -> Staff:
        lang_map = await self.get_language_map(db)

        # Validate department & position
        dept = await db.get(Department, data.department_id)
        if not dept or dept.deleted_at is not None:
            raise BadRequestException("Bộ môn được chọn không hợp lệ")

        pos = await db.get(Position, data.position_id)
        if not pos or pos.deleted_at is not None:
            raise BadRequestException("Chức vụ được chọn không hợp lệ")

        # Validate academic_title & degree if provided
        if data.academic_title_id:
            title = await db.get(AcademicTitle, data.academic_title_id)
            if not title or title.deleted_at is not None:
                raise BadRequestException("Học hàm được chọn không hợp lệ")

        if data.degree_id:
            deg = await db.get(Degree, data.degree_id)
            if not deg or deg.deleted_at is not None:
                raise BadRequestException("Học vị được chọn không hợp lệ")

        # Sinh unique slug cho Staff từ full_name
        base_slug = self.slugify(data.full_name)
        slug = base_slug
        slug_exists = await db.execute(
            select(Staff).where(Staff.slug == slug, Staff.deleted_at.is_(None))
        )
        if slug_exists.scalar_one_or_none():
            slug = f"{base_slug}-{uuid.uuid4().hex[:4]}"

        # Tự động đẩy các staff có sort_order >= data.sort_order TRONG CÙNG DEPARTMENT
        from sqlalchemy import update
        await db.execute(
            update(Staff)
            .where(
                Staff.deleted_at.is_(None),
                Staff.department_id == data.department_id,
                Staff.sort_order >= data.sort_order
            )
            .values(sort_order=Staff.sort_order + 1)
        )

        staff = Staff(
            department_id=data.department_id,
            position_id=data.position_id,
            academic_title_id=data.academic_title_id,
            degree_id=data.degree_id,
            full_name=data.full_name,
            english_name=data.english_name,
            slug=slug,
            avatar_object_key=data.avatar_object_key,
            email=data.email,
            phone=data.phone,
            website=data.website,
            office=data.office,
            sort_order=data.sort_order,
            is_active=data.is_active,
        )
        db.add(staff)
        await db.flush()

        for code, trans_data in data.translations.items():
            if code not in lang_map:
                continue
            
            trans = StaffTranslation(
                staff_id=staff.id,
                language_id=lang_map[code],
                biography=trans_data.biography,
                research_interests=trans_data.research_interests,
            )
            db.add(trans)

        await db.flush()
        db.expire(staff, ["academic_title", "degree"])
        # Load lại đầy đủ
        return await self.get_staff(db, staff.id, lang="vi")

    async def update_staff(self, db: AsyncSession, staff_id: uuid.UUID, data: StaffUpdate) -> Staff:
        staff = await self.get_staff(db, staff_id)
        lang_map = await self.get_language_map(db)

        # Kiểm tra validation của department_id mới trước
        new_dept_id = staff.department_id
        if data.department_id is not None:
            dept = await db.get(Department, data.department_id)
            if not dept or dept.deleted_at is not None:
                raise BadRequestException("Bộ môn được chọn không hợp lệ")
            new_dept_id = data.department_id

        if data.position_id is not None:
            pos = await db.get(Position, data.position_id)
            if not pos or pos.deleted_at is not None:
                raise BadRequestException("Chức vụ được chọn không hợp lệ")
            staff.position_id = data.position_id

        if data.academic_title_id is not None:
            if data.academic_title_id:
                title = await db.get(AcademicTitle, data.academic_title_id)
                if not title or title.deleted_at is not None:
                    raise BadRequestException("Học hàm được chọn không hợp lệ")
            staff.academic_title_id = data.academic_title_id

        if data.degree_id is not None:
            if data.degree_id:
                deg = await db.get(Degree, data.degree_id)
                if not deg or deg.deleted_at is not None:
                    raise BadRequestException("Học vị được chọn không hợp lệ")
            staff.degree_id = data.degree_id

        if data.full_name is not None:
            staff.full_name = data.full_name
            # Cập nhật slug mới
            base_slug = self.slugify(data.full_name)
            slug = base_slug
            slug_exists = await db.execute(
                select(Staff).where(
                    Staff.slug == slug,
                    Staff.id != staff.id,
                    Staff.deleted_at.is_(None)
                )
            )
            if slug_exists.scalar_one_or_none():
                slug = f"{base_slug}-{uuid.uuid4().hex[:4]}"
            staff.slug = slug

        if data.english_name is not None:
            staff.english_name = data.english_name
        if data.avatar_object_key is not None:
            staff.avatar_object_key = data.avatar_object_key
        if data.email is not None:
            staff.email = data.email
        if data.phone is not None:
            staff.phone = data.phone
        if data.website is not None:
            staff.website = data.website
        if data.office is not None:
            staff.office = data.office

        # Xử lý sort_order và department_id
        old_dept_id = staff.department_id
        old_sort = staff.sort_order
        new_sort = data.sort_order

        if old_dept_id != new_dept_id or (new_sort is not None and new_sort != old_sort):
            # 1. TRƯỜNG HỢP THAY ĐỔI BỘ MÔN
            if old_dept_id != new_dept_id:
                # A. Dồn thứ tự ở bộ môn cũ
                stmt_old = (
                    select(Staff)
                    .where(Staff.deleted_at.is_(None), Staff.department_id == old_dept_id, Staff.id != staff.id)
                    .order_by(Staff.sort_order.asc(), Staff.created_at.desc())
                )
                res_old = await db.execute(stmt_old)
                old_dept_staffs = list(res_old.scalars().all())
                for index, s in enumerate(old_dept_staffs):
                    s.sort_order = index

                # B. Chèn vào bộ môn mới
                stmt_new = (
                    select(Staff)
                    .where(Staff.deleted_at.is_(None), Staff.department_id == new_dept_id, Staff.id != staff.id)
                    .order_by(Staff.sort_order.asc(), Staff.created_at.desc())
                )
                res_new = await db.execute(stmt_new)
                new_dept_staffs = list(res_new.scalars().all())

                if new_sort is None:
                    new_sort = len(new_dept_staffs)
                else:
                    new_sort = max(0, min(new_sort, len(new_dept_staffs)))
                
                staff.department_id = new_dept_id
                new_dept_staffs.insert(new_sort, staff)

                # Re-index toàn bộ danh sách bộ môn mới
                for index, s in enumerate(new_dept_staffs):
                    s.sort_order = index

            # 2. TRƯỜNG HỢP CÙNG BỘ MÔN NHƯNG THAY ĐỔI THỨ TỰ
            else:
                stmt_same = (
                    select(Staff)
                    .where(Staff.deleted_at.is_(None), Staff.department_id == old_dept_id, Staff.id != staff.id)
                    .order_by(Staff.sort_order.asc(), Staff.created_at.desc())
                )
                res_same = await db.execute(stmt_same)
                same_dept_staffs = list(res_same.scalars().all())

                new_sort = max(0, min(new_sort, len(same_dept_staffs)))
                same_dept_staffs.insert(new_sort, staff)

                # Re-index toàn bộ danh sách trong bộ môn
                for index, s in enumerate(same_dept_staffs):
                    s.sort_order = index

        if data.is_active is not None:
            staff.is_active = data.is_active

        if data.translations is not None:
            for code, trans_data in data.translations.items():
                if code not in lang_map:
                    continue

                matched = None
                for t in staff.translations:
                    if t.language.code == code:
                        matched = t
                        break

                if matched:
                    matched.biography = trans_data.biography
                    matched.research_interests = trans_data.research_interests
                else:
                    new_trans = StaffTranslation(
                        staff_id=staff.id,
                        language_id=lang_map[code],
                        biography=trans_data.biography,
                        research_interests=trans_data.research_interests,
                    )
                    db.add(new_trans)

        await db.flush()
        db.expire(staff, ["academic_title", "degree"])
        return await self.get_staff(db, staff.id, lang="vi")

    async def delete_staff(self, db: AsyncSession, staff_id: uuid.UUID) -> None:
        staff = await self.get_staff(db, staff_id)
        
        # Dồn thứ tự các giảng viên đứng sau trong bộ môn
        from sqlalchemy import update
        await db.execute(
            update(Staff)
            .where(
                Staff.deleted_at.is_(None),
                Staff.department_id == staff.department_id,
                Staff.sort_order > staff.sort_order
            )
            .values(sort_order=Staff.sort_order - 1)
        )
        
        staff.deleted_at = datetime.now(UTC)
        await db.flush()

    async def get_stats(self, db: AsyncSession) -> dict:
        from app.modules.department.models import Department
        from app.modules.position.models import Position
        from app.modules.staff.models import Staff
        from sqlalchemy import func

        # 1. Department stats
        dept_total = (await db.execute(select(func.count(Department.id)).where(Department.deleted_at.is_(None)))).scalar() or 0
        dept_active = (await db.execute(select(func.count(Department.id)).where(Department.deleted_at.is_(None), Department.is_active == True))).scalar() or 0
        dept_inactive = dept_total - dept_active

        # 2. Position stats
        pos_total = (await db.execute(select(func.count(Position.id)).where(Position.deleted_at.is_(None)))).scalar() or 0
        pos_active = (await db.execute(select(func.count(Position.id)).where(Position.deleted_at.is_(None), Position.is_active == True))).scalar() or 0
        pos_inactive = pos_total - pos_active

        # 3. Staff stats
        staff_total = (await db.execute(select(func.count(Staff.id)).where(Staff.deleted_at.is_(None)))).scalar() or 0
        staff_active = (await db.execute(select(func.count(Staff.id)).where(Staff.deleted_at.is_(None), Staff.is_active == True))).scalar() or 0
        staff_inactive = staff_total - staff_active

        return {
            "departments": {"total": dept_total, "active": dept_active, "inactive": dept_inactive},
            "positions": {"total": pos_total, "active": pos_active, "inactive": pos_inactive},
            "staffs": {"total": staff_total, "active": staff_active, "inactive": staff_inactive},
        }


staff_service = StaffService()
