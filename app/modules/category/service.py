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
    CategoryResponse,
    CategoryTreeNode,
    CategoryUpdate,
)
from app.modules.category.utils import generate_slug


class CategoryService:
    """Nghiệp vụ quản lý danh mục và cấu hình SEO."""

    async def _ensure_seo_columns(self, db: AsyncSession) -> None:
        """Đảm bảo các cột SEO mới (seo_canonical, seo_robots, seo_og_image_id) tồn tại trong bảng categories."""
        try:
            from sqlalchemy import text
            async with db.begin_nested():
                await db.execute(text("SELECT seo_canonical, seo_robots, seo_og_image_id FROM categories LIMIT 1;"))
        except Exception:
            from sqlalchemy import text
            columns_to_add = [
                ("seo_canonical", "VARCHAR(255)"),
                ("seo_robots", "VARCHAR(50) DEFAULT 'index, follow'"),
                ("seo_og_image_id", "UUID REFERENCES media_items(id) ON DELETE SET NULL")
            ]
            for col_name, col_type in columns_to_add:
                try:
                    async with db.begin_nested():
                        # Cú pháp SQLite/PostgreSQL tương thích
                        await db.execute(text(f"ALTER TABLE categories ADD COLUMN {col_name} {col_type};"))
                except Exception as ex:
                    logger.warning(f"Category auto-migrate: Column {col_name} alter failed: {str(ex)}")
            try:
                await db.commit()
                logger.info("Successfully added new SEO columns to categories table.")
            except Exception as commit_ex:
                logger.warning(f"Failed to commit category schema alterations: {str(commit_ex)}")

    async def list_categories(
        self, db: AsyncSession, search: Optional[str] = None, status: Optional[str] = None
    ) -> list[Category]:
        """Lấy danh sách phẳng tất cả danh mục chưa bị xóa mềm."""
        await self._ensure_seo_columns(db)
        query = select(Category).where(Category.deleted_at == None).options(
            selectinload(Category.thumbnail),
            selectinload(Category.seo_og_image)
        )
        
        if search:
            query = query.where(Category.name.ilike(f"%{search}%"))
        if status:
            query = query.where(Category.status == status)
            
        query = query.order_by(Category.sort_order, Category.created_at)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_category_by_id(self, db: AsyncSession, category_id: uuid.UUID) -> Category:
        """Lấy chi tiết danh mục theo ID. Hỗ trợ soft-delete check."""
        await self._ensure_seo_columns(db)
        query = select(Category).where(Category.id == category_id, Category.deleted_at == None).options(
            selectinload(Category.thumbnail),
            selectinload(Category.seo_og_image)
        )
        result = await db.execute(query)
        category = result.scalar_one_or_none()
        if not category:
            raise NotFoundException(
                message="Không tìm thấy danh mục hoặc danh mục đã bị xóa",
                error_code="CATEGORY_NOT_FOUND",
                details={"category_id": str(category_id)},
            )
        return category

    async def _resolve_unique_slug(self, db: AsyncSession, base_text: str, current_id: Optional[uuid.UUID] = None) -> str:
        """Tính toán slug không trùng lặp toàn bảng (tự động tăng chỉ số -1, -2...)."""
        base_slug = generate_slug(base_text)
        if not base_slug:
            base_slug = "danh-muc"
            
        slug_candidate = base_slug
        counter = 1

        while True:
            # Kiểm tra xem slug_candidate có tồn tại ở bản ghi nào khác không
            query = select(Category.id).where(
                Category.slug == slug_candidate
            )
            if current_id:
                query = query.where(Category.id != current_id)
                
            result = await db.execute(query)
            exists = result.scalar_one_or_none()
            
            if not exists:
                break
                
            slug_candidate = f"{base_slug}-{counter}"
            counter += 1

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
        """Tạo danh mục mới, tự động sinh slug và SEO nếu thiếu."""
        await self._ensure_seo_columns(db)
        # 1. Kiểm tra danh mục cha tồn tại
        if data.parent_id is not None:
            await self.get_category_by_id(db, data.parent_id)

        # 2. Xử lý Slug
        slug = await self._resolve_unique_slug(db, data.slug or data.name)

        # 3. Tạo Category object
        category_data = data.model_dump()
        category_data["slug"] = slug
        category_data["created_by"] = current_user_id
        category_data["updated_by"] = current_user_id

        category = Category(**category_data)
        db.add(category)
        await db.flush()
        
        logger.info(f"Created category: {category.name} (slug={category.slug})")
        return category

    async def update_category(
        self, db: AsyncSession, category_id: uuid.UUID, data: CategoryUpdate, current_user_id: uuid.UUID
    ) -> Category:
        """Cập nhật thông tin danh mục, validate liên kết vòng lặp và trùng slug."""
        category = await self.get_category_by_id(db, category_id)
        update_data = data.model_dump(exclude_unset=True)

        # 1. Validate parent_id
        if "parent_id" in update_data and update_data["parent_id"] is not None:
            new_parent_id = update_data["parent_id"]
            await self.get_category_by_id(db, new_parent_id)
            await self._check_circular_reference(db, category_id, new_parent_id)

        # 2. Xử lý Slug nếu có thay đổi hoặc đổi tên mà không chỉ định slug
        if "slug" in update_data or "name" in update_data:
            new_slug_input = update_data.get("slug") or update_data.get("name") or category.name
            update_data["slug"] = await self._resolve_unique_slug(db, new_slug_input, current_id=category_id)

        # 3. Áp dụng cập nhật
        for field, value in update_data.items():
            setattr(category, field, value)
            
        category.updated_by = current_user_id
        category.updated_at = datetime.now(UTC)

        db.add(category)
        await db.flush()
        
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

        # 2. Chặn xóa nếu còn bài viết đang gán vào danh mục này (Đánh dấu TODO cho module Article)
        # TODO: Khi có module articles, kiểm tra: select(Article.id).where(Article.category_id == category_id)
        # if articles_exist: raise BadRequestException("Danh mục có bài viết hoạt động", "CATEGORY_HAS_ARTICLES")

        # 3. Tiến hành Soft Delete
        category.deleted_at = datetime.now(UTC)
        category.deleted_by = current_user_id
        
        db.add(category)
        await db.flush()
        
        logger.info(f"Soft deleted category: {category.name} (id={category_id}) by user {current_user_id}")

    # ──────────────────────────────────────────
    # Tree & Reorder
    # ──────────────────────────────────────────

    async def get_category_tree(self, db: AsyncSession) -> list[CategoryTreeNode]:
        """Lấy toàn bộ cây danh mục phục vụ render phân cấp."""
        await self._ensure_seo_columns(db)
        query = select(Category).where(Category.deleted_at == None).order_by(Category.sort_order).options(
            selectinload(Category.thumbnail),
            selectinload(Category.seo_og_image)
        )
        result = await db.execute(query)
        items = list(result.scalars().all())

        return self._build_tree(items)

    def _build_tree(self, items: list[Category]) -> list[CategoryTreeNode]:
        """Dựng cấu trúc đệ quy từ flat list danh mục."""
        node_map: dict[uuid.UUID, CategoryTreeNode] = {}
        root_nodes: list[CategoryTreeNode] = []

        for item in items:
            node = CategoryTreeNode.model_validate(item)
            node.children = []
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

    async def check_slug_uniqueness(self, db: AsyncSession, slug: str, exclude_id: Optional[uuid.UUID] = None) -> dict:
        """Kiểm tra xem slug có trùng lặp không và trả về đề xuất slug mới không trùng."""
        suggested = await self._resolve_unique_slug(db, slug, current_id=exclude_id)
        exists = (suggested != slug)
        return {
            "exists": exists,
            "suggested_slug": suggested
        }


category_service = CategoryService()
