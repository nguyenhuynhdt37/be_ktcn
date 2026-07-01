from __future__ import annotations
import uuid
from datetime import datetime, UTC
from typing import Optional

from loguru import logger
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException
from app.modules.category.models import Category
from app.modules.category.schemas import (
    CategoryCreate,
    CategoryReorderRequest,
    CategoryUpdate,
)
from app.modules.category.utils import generate_slug


class CategoryNode:
    """Class trung gian để build cây danh mục trong Service (tránh ràng buộc chặt chẽ với Pydantic schemas)."""
    def __init__(self, item: Category):
        self.id = item.id
        self.parent_id = item.parent_id
        self.thumbnail_id = item.thumbnail_id
        self.status = item.status
        self.sort_order = item.sort_order
        self.is_visible = item.is_visible
        self.is_weekly_schedule = item.is_weekly_schedule
        self.article_count = getattr(item, "article_count", 0)
        self.translations = getattr(item, "translations", [])
        self.name = getattr(item, "name", "")
        self.slug = getattr(item, "slug", "")
        self.description = getattr(item, "description", None)
        self.seo_title = getattr(item, "seo_title", None)
        self.seo_description = getattr(item, "seo_description", None)
        self.children = []


class CategoryService:
    """Nghiệp vụ quản lý danh mục và cấu hình SEO."""

    async def _ensure_seo_columns(self, db: AsyncSession) -> None:
        """Đã tối giản SEO, không sử dụng các cột cũ nữa."""
        pass

    def _apply_translation(self, category: Category, lang: str = "vi") -> Category:
        """
        Đọc bản dịch của ngôn ngữ chỉ định (hoặc fallback tiếng Việt) từ translations
        và gán vào các thuộc tính phẳng của Category.
        """
        if not category:
            return category
        
        # 1. Tìm bản dịch của ngôn ngữ đích (lang)
        target_translation = None
        for t in getattr(category, "translations", []):
            if t.language and t.language.code == lang:
                target_translation = t
                break
        
        # 2. Nếu không tìm thấy hoặc bản dịch đó rỗng tên, fallback về tiếng Việt ("vi")
        if (not target_translation or not target_translation.name) and lang != "vi":
            for t in getattr(category, "translations", []):
                if t.language and t.language.code == "vi":
                    target_translation = t
                    break
                    
        # 3. Gán thuộc tính
        if target_translation:
            category.name = target_translation.name
            category.slug = target_translation.slug
            category.description = target_translation.description
            category.seo_title = target_translation.seo_title
            category.seo_description = target_translation.seo_description
        else:
            category.name = "Chưa dịch"
            category.slug = f"chua-dich-{category.id}"
            category.description = ""
            category.seo_title = ""
            category.seo_description = ""
            
        return category

    async def list_categories(
        self, db: AsyncSession, search: Optional[str] = None, status: Optional[str] = None, only_has_articles: bool = False, lang: str = "vi"
    ) -> list[Category]:
        """Lấy danh sách phẳng tất cả danh mục chưa bị xóa mềm."""
        await self._ensure_seo_columns(db)
        from app.modules.category.models import CategoryTranslation
        from app.modules.language.models import Language
        
        query = select(Category).where(Category.deleted_at.is_(None)).options(
            selectinload(Category.thumbnail),
            selectinload(Category.translations).selectinload(CategoryTranslation.language)
        )
        
        if search:
            query = query.join(Category.translations).join(CategoryTranslation.language).where(
                Language.code == "vi",
                CategoryTranslation.name.ilike(f"%{search}%")
            )
        if status:
            query = query.where(Category.status == status)
            
        if only_has_articles:
            from app.modules.article.models import Article, ArticleStatus
            has_articles_filter = Category.id.in_(
                select(Article.category_id)
                .where(
                    Article.deleted_at.is_(None),
                    Article.is_draft.is_(False),
                    Article.status == ArticleStatus.PUBLISHED
                )
            )
            query = query.where(has_articles_filter)
            
        query = query.order_by(Category.sort_order, Category.created_at)
        result = await db.execute(query)
        categories = list(result.scalars().all())

        # Tính toán article_count cho mỗi category (đếm tất cả bài viết chưa bị soft delete)
        from app.modules.article.models import Article
        from sqlalchemy import func
        counts_query = (
            select(Article.category_id, func.count(Article.id))
            .where(
                Article.deleted_at.is_(None)
            )
            .group_by(Article.category_id)
        )
        counts_res = await db.execute(counts_query)
        counts_map = {row[0]: row[1] for row in counts_res.all() if row[0] is not None}

        for cat in categories:
            cat.article_count = counts_map.get(cat.id, 0)
            self._apply_translation(cat, lang=lang)

        return categories

    async def get_category_by_id(self, db: AsyncSession, category_id: uuid.UUID, lang: str = "vi") -> Category:
        """Lấy chi tiết danh mục theo ID. Hỗ trợ soft-delete check."""
        await self._ensure_seo_columns(db)
        from app.modules.category.models import CategoryTranslation
        query = select(Category).where(Category.id == category_id, Category.deleted_at == None).options(
            selectinload(Category.thumbnail),
            selectinload(Category.translations).selectinload(CategoryTranslation.language)
        )
        result = await db.execute(query)
        category = result.scalar_one_or_none()
        if not category:
            raise NotFoundException(
                message="Không tìm thấy danh mục hoặc danh mục đã bị xóa",
                error_code="CATEGORY_NOT_FOUND",
                details={"category_id": str(category_id)},
            )

        # Tính toán article_count cho category này (đếm tất cả bài viết chưa bị soft delete)
        from app.modules.article.models import Article
        from sqlalchemy import func
        count_query = (
            select(func.count(Article.id))
            .where(
                Article.category_id == category_id,
                Article.deleted_at.is_(None)
            )
        )
        count_res = await db.execute(count_query)
        category.article_count = count_res.scalar() or 0
        self._apply_translation(category, lang=lang)

        return category

    async def _resolve_unique_slug(
        self, db: AsyncSession, base_text: str, language_id: uuid.UUID, current_id: Optional[uuid.UUID] = None
    ) -> str:
        """Tính toán slug không trùng lặp trong bảng CategoryTranslation theo từng ngôn ngữ."""
        base_slug = generate_slug(base_text)
        if not base_slug:
            base_slug = "danh-muc"
            
        slug_candidate = base_slug
        
        from app.modules.category.models import CategoryTranslation
        # Check xem slug đã tồn tại cho language_id này chưa
        query = select(CategoryTranslation.slug).where(
            CategoryTranslation.language_id == language_id,
            CategoryTranslation.slug == slug_candidate
        )
        if current_id:
            query = query.where(CategoryTranslation.category_id != current_id)
            
        res = await db.execute(query)
        exists = res.scalar_one_or_none()
        
        if exists:
            # Sinh slug mới bằng cách thêm uuid rút gọn
            import uuid as py_uuid
            suffix = str(py_uuid.uuid4())[:8]
            slug_candidate = f"{base_slug}-{suffix}"
            
        return slug_candidate

    async def _check_circular_reference(self, db: AsyncSession, category_id: uuid.UUID, new_parent_id: uuid.UUID) -> None:
        """Kiểm tra đệ quy ngược lên tổ tiên để ngăn chặn liên kết vòng lặp."""
        if category_id == new_parent_id:
            raise BadRequestException(
                message="Không thể gán danh mục cha làm chính nó",
                error_code="CIRCULAR_REFERENCE"
            )

        curr_parent_id = new_parent_id
        visited = set()

        while curr_parent_id is not None:
            if curr_parent_id == category_id:
                raise BadRequestException(
                    message="Phát hiện liên kết vòng lặp cấu trúc cây danh mục",
                    error_code="CIRCULAR_REFERENCE"
                )
            if curr_parent_id in visited:
                break
            visited.add(curr_parent_id)

            query = select(Category.parent_id).where(
                Category.id == curr_parent_id, 
                Category.deleted_at == None
            )
            result = await db.execute(query)
            row = result.one_or_none()
            curr_parent_id = row[0] if row else None

    async def create_category(self, db: AsyncSession, data: CategoryCreate, current_user_id: uuid.UUID) -> Category:
        """Tạo danh mục mới đa ngôn ngữ thực thụ."""
        await self._ensure_seo_columns(db)
        if data.parent_id is not None:
            await self.get_category_by_id(db, data.parent_id)

        # 1. Tạo Category object chính (Shared settings)
        category_data = {
            "parent_id": data.parent_id,
            "thumbnail_id": data.thumbnail_id,
            "status": data.status or "ACTIVE",
            "sort_order": data.sort_order or 0,
            "is_visible": data.is_visible if data.is_visible is not None else True,
            "is_weekly_schedule": data.is_weekly_schedule if data.is_weekly_schedule is not None else False,
            "created_by": current_user_id,
            "updated_by": current_user_id
        }

        category = Category(**category_data)
        db.add(category)
        await db.flush()

        # 2. Lưu các bản dịch translations
        from app.modules.language.models import Language
        from app.modules.category.models import CategoryTranslation

        # Lấy tất cả ngôn ngữ trong hệ thống
        lang_res = await db.execute(select(Language))
        languages = lang_res.scalars().all()
        lang_map = {l.code: l.id for l in languages}

        for lang_code, trans_data in data.translations.items():
            lang_id = lang_map.get(lang_code)
            if not lang_id:
                continue

            # Sinh slug độc bản cho ngôn ngữ này
            slug = await self._resolve_unique_slug(db, trans_data.slug or trans_data.name, lang_id)

            # Tạo bản dịch
            translation = CategoryTranslation(
                category_id=category.id,
                language_id=lang_id,
                name=trans_data.name,
                slug=slug,
                description=trans_data.description,
                seo_title=trans_data.seo_title or trans_data.name[:60],
                seo_description=trans_data.seo_description or (trans_data.description[:160] if trans_data.description else None)
            )
            db.add(translation)
        
        await db.flush()
        db.expire(category, ["translations"])

        # Load lại Category với đầy đủ translations
        query = select(Category).where(Category.id == category.id).options(
            selectinload(Category.translations).selectinload(CategoryTranslation.language)
        )
        res = await db.execute(query)
        category = res.scalar_one()

        category.article_count = 0
        self._apply_translation(category)
        return category

    async def update_category(
        self, db: AsyncSession, category_id: uuid.UUID, data: CategoryUpdate, current_user_id: uuid.UUID
    ) -> Category:
        """Cập nhật thông tin danh mục và các bản dịch đa ngôn ngữ chi tiết."""
        category = await self.get_category_by_id(db, category_id)
        update_data = data.model_dump(exclude_unset=True)

        if "parent_id" in update_data and update_data["parent_id"] is not None:
            new_parent_id = update_data["parent_id"]
            await self.get_category_by_id(db, new_parent_id)
            await self._check_circular_reference(db, category_id, new_parent_id)

        # Cập nhật các trường dùng chung ở root
        for field in ["parent_id", "thumbnail_id", "status", "sort_order", "is_visible", "is_weekly_schedule"]:
            if field in update_data:
                setattr(category, field, update_data[field])

        category.updated_by = current_user_id
        category.updated_at = datetime.now(UTC)
        db.add(category)

        # Cập nhật các bản dịch translations
        if "translations" in update_data and update_data["translations"]:
            from app.modules.language.models import Language
            from app.modules.category.models import CategoryTranslation

            # Lấy tất cả ngôn ngữ
            lang_res = await db.execute(select(Language))
            languages = lang_res.scalars().all()
            lang_map = {l.code: l.id for l in languages}

            for lang_code, trans_dict in update_data["translations"].items():
                lang_id = lang_map.get(lang_code)
                if not lang_id:
                    continue

                # Tìm bản dịch cũ
                trans_query = select(CategoryTranslation).where(
                    CategoryTranslation.category_id == category_id,
                    CategoryTranslation.language_id == lang_id
                )
                trans_res = await db.execute(trans_query)
                translation = trans_res.scalar_one_or_none()

                name_val = trans_dict.get("name")
                slug_val = trans_dict.get("slug")
                desc_val = trans_dict.get("description")
                seo_title_val = trans_dict.get("seo_title")
                seo_desc_val = trans_dict.get("seo_description")

                # Nếu là tạo mới bản dịch cho ngôn ngữ này
                if not translation:
                    if name_val:
                        final_slug = await self._resolve_unique_slug(db, slug_val or name_val, lang_id)
                        translation = CategoryTranslation(
                            category_id=category_id,
                            language_id=lang_id,
                            name=name_val,
                            slug=final_slug,
                            description=desc_val,
                            seo_title=seo_title_val or name_val[:60],
                            seo_description=seo_desc_val or (desc_val[:160] if desc_val else None)
                        )
                        db.add(translation)
                else:
                    # Nếu cập nhật bản dịch cũ
                    if name_val is not None:
                        translation.name = name_val
                    if slug_val is not None:
                        translation.slug = await self._resolve_unique_slug(db, slug_val, lang_id, current_id=category_id)
                    elif name_val is not None:
                        translation.slug = await self._resolve_unique_slug(db, name_val, lang_id, current_id=category_id)

                    if desc_val is not None:
                        translation.description = desc_val
                    if seo_title_val is not None:
                        translation.seo_title = seo_title_val
                    if seo_desc_val is not None:
                        translation.seo_description = seo_desc_val
                    db.add(translation)

        await db.flush()
        db.expire(category, ["translations"])
        
        from app.modules.category.models import CategoryTranslation
        query = select(Category).where(Category.id == category.id).options(
            selectinload(Category.translations).selectinload(CategoryTranslation.language)
        )
        res = await db.execute(query)
        category = res.scalar_one()
        
        # Tính toán lại article_count
        from app.modules.article.models import Article
        from sqlalchemy import func
        count_query = (
            select(func.count(Article.id))
            .where(
                Article.category_id == category.id,
                Article.deleted_at.is_(None)
            )
        )
        count_res = await db.execute(count_query)
        category.article_count = count_res.scalar() or 0

        self._apply_translation(category)
        logger.info(f"Updated category: {category.name} (id={category.id})")
        return category

    async def delete_category(self, db: AsyncSession, category_id: uuid.UUID, current_user_id: uuid.UUID) -> None:
        """Xóa mềm danh mục. Kiểm tra các ràng buộc danh mục con và bài viết."""
        category = await self.get_category_by_id(db, category_id)



        # 1. Chặn xóa nếu còn danh mục con hoạt động

        children_query = select(Category.id).where(
            Category.parent_id == category_id, 
            Category.deleted_at == None
        )
        children_result = await db.execute(children_query)
        if children_result.first():
            raise BadRequestException(
                message="Không thể xóa danh mục đang có chứa danh mục con hoạt động",
                error_code="CATEGORY_HAS_CHILDREN"
            )

        # 2. Chặn xóa nếu còn bài viết đang gán vào danh mục này chưa bị xóa mềm
        from app.modules.article.models import Article
        articles_query = select(Article.id).where(
            Article.category_id == category_id,
            Article.deleted_at.is_(None)
        )
        articles_result = await db.execute(articles_query)
        if articles_result.first():
            raise BadRequestException(
                message="Không thể xóa danh mục đang có bài viết hoạt động. Vui lòng xóa hoặc di chuyển tất cả bài viết thuộc danh mục này trước.",
                error_code="CATEGORY_HAS_ACTIVE_ARTICLES",
                details={"category_id": str(category_id)}
            )

        # 3. Tiến hành Soft Delete
        category.deleted_at = datetime.now(UTC)
        category.deleted_by = current_user_id
        
        db.add(category)
        await db.flush()
        
        logger.info(f"Soft deleted category: {category.name} (id={category_id}) by user {current_user_id}")

    async def restore_category(self, db: AsyncSession, category_id: uuid.UUID, current_user_id: uuid.UUID) -> Category:
        """Khôi phục danh mục đã bị xóa mềm."""
        from app.modules.category.models import CategoryTranslation
        query = select(Category).where(Category.id == category_id).options(
            selectinload(Category.thumbnail),
            selectinload(Category.translations).selectinload(CategoryTranslation.language)
        )
        result = await db.execute(query)
        category = result.scalar_one_or_none()
        if not category:
            raise NotFoundException(
                message="Không tìm thấy danh mục để khôi phục",
                error_code="CATEGORY_NOT_FOUND",
                details={"category_id": str(category_id)},
            )

        self._apply_translation(category)

        if category.deleted_at is not None:
            category.deleted_at = None
            category.deleted_by = None
            category.updated_by = current_user_id
            category.updated_at = datetime.now(UTC)
            db.add(category)
            await db.flush()
            logger.info(f"Restored category: {category.name} (id={category_id}) by user {current_user_id}")

        # Tính toán lại article_count
        from app.modules.article.models import Article
        from sqlalchemy import func
        count_query = (
            select(func.count(Article.id))
            .where(
                Article.category_id == category.id,
                Article.deleted_at.is_(None)
            )
        )
        count_res = await db.execute(count_query)
        category.article_count = count_res.scalar() or 0

        self._apply_translation(category)
        return category

    # ──────────────────────────────────────────
    # Tree & Reorder
    # ──────────────────────────────────────────




    # ──────────────────────────────────────────
    # Tree & Reorder
    # ──────────────────────────────────────────

    async def get_category_tree(
        self, db: AsyncSession, with_article_count: bool = False, only_has_articles: bool = False, lang: str = "vi"
    ) -> list[CategoryNode]:
        """Lấy toàn bộ cây danh mục phục vụ render phân cấp."""
        await self._ensure_seo_columns(db)
        
        # Nếu yêu cầu chỉ lấy chuyên mục có bài viết, bắt buộc bật đếm tin
        effective_with_count = with_article_count or only_has_articles

        from app.modules.category.models import CategoryTranslation
        query = select(Category).where(Category.deleted_at.is_(None)).order_by(Category.sort_order).options(
            selectinload(Category.thumbnail),
            selectinload(Category.translations).selectinload(CategoryTranslation.language)
        )
        result = await db.execute(query)
        items = list(result.scalars().all())

        # Tính toán article_count cho mỗi category (đếm tất cả bài viết chưa bị soft delete)
        from app.modules.article.models import Article
        from sqlalchemy import func
        counts_query = (
            select(Article.category_id, func.count(Article.id))
            .where(
                Article.deleted_at.is_(None)
            )
            .group_by(Article.category_id)
        )
        counts_res = await db.execute(counts_query)
        counts_map = {row[0]: row[1] for row in counts_res.all() if row[0] is not None}

        for item in items:
            item.article_count = counts_map.get(item.id, 0)
            self._apply_translation(item, lang=lang)

        root_nodes = self._build_tree(items)

        # Tiến hành cắt tỉa đệ quy nếu only_has_articles = True
        if only_has_articles:
            def _prune_empty_nodes(nodes: list[CategoryNode]) -> list[CategoryNode]:
                pruned = []
                for node in nodes:
                    if node.children:
                        node.children = _prune_empty_nodes(node.children)
                    if node.article_count > 0 or len(node.children) > 0:
                        pruned.append(node)
                return pruned

            root_nodes = _prune_empty_nodes(root_nodes)

        return root_nodes

    def _build_tree(self, items: list[Category]) -> list[CategoryNode]:
        """Dựng cấu trúc đệ quy từ flat list danh mục."""
        node_map: dict[uuid.UUID, CategoryNode] = {}
        root_nodes: list[CategoryNode] = []

        for item in items:
            node = CategoryNode(item)
            node_map[item.id] = node

        for item in items:
            node = node_map[item.id]
            if item.parent_id is not None and item.parent_id in node_map:
                node_map[item.parent_id].children.append(node)
            else:
                root_nodes.append(node)

        return root_nodes

    async def reorder_categories(self, db: AsyncSession, data: CategoryReorderRequest, current_user_id: uuid.UUID) -> None:
        """Batch update kéo thả thay đổi vị trí danh mục. Bảo vệ toàn vẹn dữ liệu tránh vòng lặp."""
        await self._ensure_seo_columns(db)
        # 1. Lấy tất cả categories hoạt động để kiểm tra nhanh
        query = select(Category).where(Category.deleted_at == None)
        result = await db.execute(query)
        existing_map = {c.id: c for c in result.scalars().all()}

        # 2. Kiểm tra tồn tại
        for item in data.items:
            if item.id not in existing_map:
                raise NotFoundException(
                    message="Không tìm thấy danh mục để sắp xếp",
                    error_code="CATEGORY_NOT_FOUND",
                    details={"id": str(item.id)}
                )
            if item.parent_id is not None and item.parent_id not in existing_map:
                raise NotFoundException(
                    message="Không tìm thấy danh mục cha đích",
                    error_code="PARENT_CATEGORY_NOT_FOUND",
                    details={"parent_id": str(item.parent_id)}
                )

        # 3. Tạo parent map mới phục vụ validate vòng lặp
        new_parent_map = {}
        for item in data.items:
            new_parent_map[item.id] = item.parent_id

        # 4. Kiểm tra vòng lặp toàn bộ batch
        for item_id in new_parent_map:
            visited = set()
            curr = new_parent_map[item_id]
            while curr is not None:
                if curr == item_id:
                    raise BadRequestException(
                        message="Kéo thả tạo ra vòng lặp cấu trúc danh mục",
                        error_code="CIRCULAR_REFERENCE"
                    )
                if curr in visited:
                    break
                visited.add(curr)
                # Tiếp tục truy ngược từ reorder map hoặc DB hiện tại
                curr = new_parent_map.get(curr, existing_map[curr].parent_id if curr in existing_map else None)

        # 5. Tiến hành lưu cập nhật
        for item in data.items:
            cat = existing_map[item.id]
            cat.parent_id = item.parent_id
            cat.sort_order = item.sort_order
            cat.updated_by = current_user_id
            cat.updated_at = datetime.now(UTC)
            db.add(cat)

        logger.info(f"Batch reordered {len(data.items)} categories successfully by user {current_user_id}")

    async def check_slug_uniqueness(
        self, db: AsyncSession, slug: str, lang_code: str = "vi", exclude_id: Optional[uuid.UUID] = None
    ) -> dict:
        """Kiểm tra xem slug có trùng lặp không và trả về đề xuất slug mới không trùng."""
        from app.modules.language.models import Language
        # Lấy language_id từ code
        q = select(Language.id).where(Language.code == lang_code)
        res = await db.execute(q)
        lang_id = res.scalar_one_or_none()
        if not lang_id:
            # Fallback lấy vi
            q_vi = select(Language.id).where(Language.code == "vi")
            res_vi = await db.execute(q_vi)
            lang_id = res_vi.scalar_one_or_none()

        suggested = await self._resolve_unique_slug(db, slug, lang_id, current_id=exclude_id)
        exists = (suggested != slug)
        return {
            "exists": exists,
            "suggested_slug": suggested
        }


category_service = CategoryService()
