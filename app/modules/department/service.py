import re
import uuid
from datetime import UTC, datetime
from typing import Optional, Tuple
from sqlalchemy import select, func, or_, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import BadRequestException, NotFoundException
from app.modules.department.models import Department, DepartmentTranslation
from app.modules.department.schemas import DepartmentCreate, DepartmentUpdate
from app.modules.language.models import Language


class DepartmentService:
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

    def _apply_translation(self, department: Department, lang: str = "vi") -> Department:
        """Gán các thuộc tính động (name, description, slug, ...) dựa trên ngôn ngữ yêu cầu."""
        matched = None
        for t in department.translations:
            if t.language.code == lang:
                matched = t
                break
        
        # Fallback về tiếng Việt nếu không có ngôn ngữ yêu cầu
        if not matched and lang != "vi":
            for t in department.translations:
                if t.language.code == "vi":
                    matched = t
                    break
        
        # Fallback về bản dịch đầu tiên có sẵn
        if not matched and department.translations:
            matched = department.translations[0]

        department.name = matched.name if matched else ""
        department.description = matched.description if matched else None
        department.short_description = matched.short_description if matched else None
        department.mission = matched.mission if matched else None
        department.vision = matched.vision if matched else None
        department.history = matched.history if matched else None
        department.research_overview = matched.research_overview if matched else None
        department.seo_title = matched.seo_title if matched else None
        department.seo_description = matched.seo_description if matched else None
        department.slug = matched.slug if matched else ""
        return department

    async def _validate_head_staff(self, db: AsyncSession, head_staff_id: uuid.UUID) -> None:
        """Kiểm tra head_staff_id tồn tại trong bảng staffs."""
        from app.modules.staff.models import Staff
        stmt = select(Staff.id).where(Staff.id == head_staff_id, Staff.deleted_at.is_(None))
        result = await db.execute(stmt)
        if not result.scalar_one_or_none():
            raise BadRequestException(f"Không tìm thấy giảng viên với ID: {head_staff_id}")

    async def list_departments(
        self,
        db: AsyncSession,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        sort_by: str = "sort_order",
        order: str = "asc",
        page: int = 1,
        page_size: int = 10,
        lang: str = "vi",
    ) -> Tuple[list[Department], int]:
        # Xây dựng query cơ bản
        stmt = select(Department).where(Department.deleted_at.is_(None))

        if is_active is not None:
            stmt = stmt.where(Department.is_active == is_active)

        if search:
            # Tìm kiếm qua tên hoặc mô tả trong bảng dịch
            stmt = stmt.join(DepartmentTranslation).where(
                or_(
                    DepartmentTranslation.name.ilike(f"%{search}%"),
                    DepartmentTranslation.description.ilike(f"%{search}%"),
                )
            ).distinct()

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await db.execute(count_stmt)
        total_count = total.scalar() or 0

        # Sort & Pagination
        if sort_by == "name" and search:
            # Sort theo name translation
            if order == "desc":
                stmt = stmt.order_by(DepartmentTranslation.name.desc())
            else:
                stmt = stmt.order_by(DepartmentTranslation.name.asc())
        else:
            sort_attr = getattr(Department, sort_by, Department.sort_order)
            if order == "desc":
                stmt = stmt.order_by(sort_attr.desc())
            else:
                stmt = stmt.order_by(sort_attr.asc())

        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        result = await db.execute(stmt)
        departments = result.scalars().all()

        # Tính toán staff_count cho mỗi bộ môn
        from app.modules.staff.models import Staff
        counts_query = (
            select(Staff.department_id, func.count(Staff.id))
            .where(Staff.deleted_at.is_(None))
            .group_by(Staff.department_id)
        )
        counts_res = await db.execute(counts_query)
        counts_map = {row[0]: row[1] for row in counts_res.all() if row[0] is not None}

        for dept in departments:
            self._apply_translation(dept, lang=lang)
            dept.staff_count = counts_map.get(dept.id, 0)

        return list(departments), total_count

    async def get_department(self, db: AsyncSession, department_id: uuid.UUID, lang: str = "vi") -> Department:
        stmt = select(Department).where(Department.id == department_id, Department.deleted_at.is_(None))
        result = await db.execute(stmt)
        dept = result.scalar_one_or_none()
        if not dept:
            raise NotFoundException("Không tìm thấy bộ môn")
        self._apply_translation(dept, lang=lang)

        # Tính toán staff_count
        from app.modules.staff.models import Staff
        count_query = (
            select(func.count(Staff.id))
            .where(Staff.deleted_at.is_(None), Staff.department_id == department_id)
        )
        count_res = await db.execute(count_query)
        dept.staff_count = count_res.scalar() or 0

        return dept

    async def get_department_by_slug(self, db: AsyncSession, slug: str, lang: str = "vi") -> Department:
        stmt = (
            select(Department)
            .join(DepartmentTranslation)
            .join(Language, DepartmentTranslation.language_id == Language.id)
            .where(
                DepartmentTranslation.slug == slug,
                Language.code == lang,
                Department.deleted_at.is_(None)
            )
        )
        result = await db.execute(stmt)
        dept = result.scalar_one_or_none()
        if not dept:
            raise NotFoundException("Không tìm thấy bộ môn")
        self._apply_translation(dept, lang=lang)

        # Tính toán staff_count
        from app.modules.staff.models import Staff
        count_query = (
            select(func.count(Staff.id))
            .where(Staff.deleted_at.is_(None), Staff.department_id == dept.id)
        )
        count_res = await db.execute(count_query)
        dept.staff_count = count_res.scalar() or 0

        return dept

    async def create_department(self, db: AsyncSession, data: DepartmentCreate) -> Department:
        lang_map = await self.get_language_map(db)
        
        # 0. Validate thumbnail
        if not data.thumbnail_object_key or not data.thumbnail_object_key.strip():
            raise BadRequestException("Ảnh đại diện (thumbnail) là bắt buộc")

        # 1. Validate translations
        if "vi" not in data.translations or not data.translations["vi"].name.strip():
            raise BadRequestException("Bản dịch tiếng Việt (vi) là bắt buộc và không được để trống tên")
        if "en" not in data.translations or not data.translations["en"].name.strip():
            raise BadRequestException("Bản dịch tiếng Anh (en) là bắt buộc và không được để trống tên")

        # 2. Validate head_staff_id nếu có
        if data.head_staff_id:
            await self._validate_head_staff(db, data.head_staff_id)

        # 3. Tự động đẩy các department có sort_order >= data.sort_order
        from sqlalchemy import update
        await db.execute(
            update(Department)
            .where(Department.deleted_at.is_(None), Department.sort_order >= data.sort_order)
            .values(sort_order=Department.sort_order + 1)
        )

        dept = Department(
            code=data.code,
            unit_type=data.unit_type,
            parent_id=data.parent_id,
            thumbnail_object_key=data.thumbnail_object_key,
            logo_object_key=data.logo_object_key,
            banner_object_key=data.banner_object_key,
            phone=data.phone,
            email=data.email,
            website=data.website,
            office=data.office,
            sort_order=data.sort_order,
            display_order=data.display_order,
            is_active=data.is_active,
            content_status=data.content_status,
            head_staff_id=data.head_staff_id,
        )
        db.add(dept)
        await db.flush()

        # 4. Tạo các translations
        for code, trans_data in data.translations.items():
            if code not in lang_map:
                continue
            if not trans_data.name:
                continue

            slug = trans_data.slug or self.slugify(trans_data.name)
            # Check slug trùng
            slug_exists = await db.execute(
                select(DepartmentTranslation).where(DepartmentTranslation.slug == slug)
            )
            if slug_exists.scalar_one_or_none():
                slug = f"{slug}-{uuid.uuid4().hex[:4]}"

            trans = DepartmentTranslation(
                department_id=dept.id,
                language_id=lang_map[code],
                name=trans_data.name,
                description=trans_data.description,
                short_description=trans_data.short_description,
                mission=trans_data.mission,
                vision=trans_data.vision,
                history=trans_data.history,
                research_overview=trans_data.research_overview,
                seo_title=trans_data.seo_title,
                seo_description=trans_data.seo_description,
                slug=slug,
            )
            db.add(trans)

        await db.flush()
        # Load lại đầy đủ
        stmt = select(Department).where(Department.id == dept.id)
        dept = (await db.execute(stmt)).scalar_one()
        self._apply_translation(dept, lang="vi")
        dept.staff_count = 0
        return dept

    async def update_department(self, db: AsyncSession, department_id: uuid.UUID, data: DepartmentUpdate) -> Department:
        dept = await self.get_department(db, department_id)
        lang_map = await self.get_language_map(db)

        # Update fields trực tiếp
        if data.code is not None:
            dept.code = data.code
        if data.unit_type is not None:
            dept.unit_type = data.unit_type
        if data.parent_id is not None:
            if data.parent_id == dept.id:
                raise BadRequestException("Đơn vị không thể là cấp trên của chính nó")
            dept.parent_id = data.parent_id
        if data.thumbnail_object_key is not None:
            dept.thumbnail_object_key = data.thumbnail_object_key
        if data.logo_object_key is not None:
            dept.logo_object_key = data.logo_object_key
        if data.banner_object_key is not None:
            dept.banner_object_key = data.banner_object_key
        if data.phone is not None:
            dept.phone = data.phone
        if data.email is not None:
            dept.email = data.email
        if data.website is not None:
            dept.website = data.website
        if data.office is not None:
            dept.office = data.office
        if data.display_order is not None:
            dept.display_order = data.display_order
        if data.head_staff_id is not None:
            await self._validate_head_staff(db, data.head_staff_id)
            dept.head_staff_id = data.head_staff_id
        if data.sort_order is not None and data.sort_order != dept.sort_order:
            # 1. Lấy tất cả bộ môn khác sắp xếp theo sort_order tăng dần
            stmt_other = (
                select(Department)
                .where(Department.deleted_at.is_(None), Department.id != dept.id)
                .order_by(Department.sort_order.asc(), Department.created_at.desc())
            )
            res_other = await db.execute(stmt_other)
            other_depts = list(res_other.scalars().all())
            
            # 2. Giới hạn index mới
            new_sort = max(0, min(data.sort_order, len(other_depts)))
            
            # 3. Chèn department hiện tại vào index mới
            other_depts.insert(new_sort, dept)
            
            # 4. Gán lại sort_order liên tục cho toàn bộ danh sách để chuẩn hóa thứ tự
            for index, d in enumerate(other_depts):
                d.sort_order = index
        if data.is_active is not None:
            dept.is_active = data.is_active
        if data.content_status is not None:
            dept.content_status = data.content_status

        # Update translations
        if data.translations is not None:
            for code, trans_data in data.translations.items():
                if code not in lang_map:
                    continue
                
                # Tìm bản dịch hiện tại
                matched = None
                for t in dept.translations:
                    if t.language.code == code:
                        matched = t
                        break

                if matched:
                    if trans_data.name:
                        matched.name = trans_data.name
                        matched.description = trans_data.description
                        matched.short_description = trans_data.short_description
                        matched.mission = trans_data.mission
                        matched.vision = trans_data.vision
                        matched.history = trans_data.history
                        matched.research_overview = trans_data.research_overview
                        matched.seo_title = trans_data.seo_title
                        matched.seo_description = trans_data.seo_description
                        if trans_data.slug:
                            # Validate slug mới nếu đổi
                            if matched.slug != trans_data.slug:
                                slug_exists = await db.execute(
                                    select(DepartmentTranslation).where(
                                        DepartmentTranslation.slug == trans_data.slug,
                                        DepartmentTranslation.id != matched.id
                                    )
                                )
                                if slug_exists.scalars().first():
                                    raise BadRequestException(f"Slug '{trans_data.slug}' đã tồn tại")
                                matched.slug = trans_data.slug
                            else:
                                matched.slug = trans_data.slug
                        else:
                             new_slug = self.slugify(trans_data.name)
                             if matched.slug != new_slug:
                                 slug_exists = await db.execute(
                                     select(DepartmentTranslation).where(
                                         DepartmentTranslation.slug == new_slug,
                                         DepartmentTranslation.id != matched.id
                                     )
                                 )
                                 if slug_exists.scalars().first():
                                     new_slug = f"{new_slug}-{uuid.uuid4().hex[:4]}"
                                 matched.slug = new_slug
                else:
                    if trans_data.name:
                        slug = trans_data.slug or self.slugify(trans_data.name)
                        slug_exists = await db.execute(
                            select(DepartmentTranslation).where(DepartmentTranslation.slug == slug)
                        )
                        if slug_exists.scalars().first():
                            slug = f"{slug}-{uuid.uuid4().hex[:4]}"

                        new_trans = DepartmentTranslation(
                            department_id=dept.id,
                            language_id=lang_map[code],
                            name=trans_data.name,
                            description=trans_data.description,
                            short_description=trans_data.short_description,
                            mission=trans_data.mission,
                            vision=trans_data.vision,
                            history=trans_data.history,
                            research_overview=trans_data.research_overview,
                            seo_title=trans_data.seo_title,
                            seo_description=trans_data.seo_description,
                            slug=slug,
                        )
                        db.add(new_trans)

        await db.flush()
        self._apply_translation(dept, lang="vi")

        # Tính toán staff_count
        from app.modules.staff.models import Staff
        count_query = (
            select(func.count(Staff.id))
            .where(Staff.deleted_at.is_(None), Staff.department_id == dept.id)
        )
        count_res = await db.execute(count_query)
        dept.staff_count = count_res.scalar() or 0

        return dept

    async def delete_department(self, db: AsyncSession, department_id: uuid.UUID) -> None:
        dept = await self.get_department(db, department_id)
        now_time = datetime.now(UTC)
        
        # Dồn thứ tự của các bộ môn đứng sau bộ môn này
        from sqlalchemy import update
        await db.execute(
            update(Department)
            .where(Department.deleted_at.is_(None), Department.sort_order > dept.sort_order)
            .values(sort_order=Department.sort_order - 1)
        )
        
        # Xóa mềm bộ môn
        dept.deleted_at = now_time
        
        # Xóa mềm toàn bộ giảng viên thuộc bộ môn đó
        from app.modules.staff.models import Staff
        await db.execute(
            update(Staff)
            .where(Staff.department_id == department_id, Staff.deleted_at.is_(None))
            .values(deleted_at=now_time)
        )
        await db.flush()

    async def get_stats(self, db: AsyncSession) -> dict:
        from sqlalchemy import func
        dept_total = (await db.execute(select(func.count(Department.id)).where(Department.deleted_at.is_(None)))).scalar() or 0
        dept_active = (await db.execute(select(func.count(Department.id)).where(Department.deleted_at.is_(None), Department.is_active == True))).scalar() or 0
        dept_inactive = dept_total - dept_active
        return {
            "total": dept_total,
            "active": dept_active,
            "inactive": dept_inactive
        }


department_service = DepartmentService()
