import uuid
from typing import Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from app.modules.menu.models import Menu, MenuItem, MenuItemTargetType
from app.modules.menu.schemas import (
    MenuCreate,
    MenuItemCreate,
    MenuItemReorderRequest,
    MenuItemResponse,
    MenuItemTreeNode,
    MenuItemUpdate,
    MenuTreeResponse,
    MenuUpdate,
    build_menu_item_resolved,
)
from app.modules.menu.target_resolver import TargetInfo, target_resolver


MAX_DEPTH = 3


class MenuService:
    """Business logic cho quản lý Menu và Menu Items."""

    # ──────────────────────────────────────────
    # Menu CRUD
    # ──────────────────────────────────────────

    async def list_menus(self, db: AsyncSession) -> list[Menu]:
        """Lấy danh sách tất cả menus."""
        query = select(Menu).order_by(Menu.created_at)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_menu_by_id(self, db: AsyncSession, menu_id: uuid.UUID) -> Menu:
        """Lấy menu theo ID. Raise NotFoundException nếu không tìm thấy."""
        query = select(Menu).where(Menu.id == menu_id)
        result = await db.execute(query)
        menu = result.scalar_one_or_none()
        if not menu:
            raise NotFoundException(
                message="Không tìm thấy menu",
                error_code="MENU_NOT_FOUND",
                details={"menu_id": str(menu_id)},
            )
        return menu

    async def get_menu_by_code(self, db: AsyncSession, code: str) -> Menu:
        """Lấy menu theo code. Raise NotFoundException nếu không tìm thấy."""
        query = select(Menu).where(Menu.code == code)
        result = await db.execute(query)
        menu = result.scalar_one_or_none()
        if not menu:
            raise NotFoundException(
                message="Không tìm thấy menu",
                error_code="MENU_NOT_FOUND",
                details={"code": code},
            )
        return menu

    async def create_menu(self, db: AsyncSession, data: MenuCreate) -> Menu:
        """Tạo menu mới. Validate code unique."""
        # Check code unique
        existing = await db.execute(select(Menu).where(Menu.code == data.code))
        if existing.scalar_one_or_none():
            raise ConflictException(
                message=f"Menu code '{data.code}' đã tồn tại",
                error_code="MENU_CODE_EXISTS",
                details={"code": data.code},
            )

        menu = Menu(**data.model_dump())
        db.add(menu)
        await db.flush()
        logger.info(f"Created menu: {menu.code} (id={menu.id})")
        return menu

    async def update_menu(
        self, db: AsyncSession, menu_id: uuid.UUID, data: MenuUpdate
    ) -> Menu:
        """Cập nhật menu. Validate code unique nếu đổi."""
        menu = await self.get_menu_by_id(db, menu_id)
        update_data = data.model_dump(exclude_unset=True)

        # Check code unique nếu thay đổi
        if "code" in update_data and update_data["code"] != menu.code:
            existing = await db.execute(
                select(Menu).where(Menu.code == update_data["code"])
            )
            if existing.scalar_one_or_none():
                raise ConflictException(
                    message=f"Menu code '{update_data['code']}' đã tồn tại",
                    error_code="MENU_CODE_EXISTS",
                    details={"code": update_data["code"]},
                )

        for field, value in update_data.items():
            setattr(menu, field, value)

        db.add(menu)
        await db.flush()
        logger.info(f"Updated menu: {menu.code} (id={menu.id})")
        return menu

    async def delete_menu(self, db: AsyncSession, menu_id: uuid.UUID) -> None:
        """Xóa menu (cascade xóa tất cả menu items)."""
        menu = await self.get_menu_by_id(db, menu_id)
        await db.delete(menu)
        await db.flush()
        logger.info(f"Deleted menu: {menu.code} (id={menu_id})")

    # ──────────────────────────────────────────
    # Menu Item CRUD
    # ──────────────────────────────────────────

    def _to_item_response(
        self, item: MenuItem, target_info: Optional[TargetInfo] = None
    ) -> MenuItemResponse:
        """Convert MenuItem model thành MenuItemResponse với computed has_link và target_info."""
        res_dict = build_menu_item_resolved(item)
        res_dict["target_info"] = target_info
        res_dict["has_link"] = item.target_type is not None or item.external_url is not None
        # Đảm bảo giữ nguyên các trường kiểu datetime nếu có
        res_dict["created_at"] = getattr(item, "created_at", None)
        res_dict["updated_at"] = getattr(item, "updated_at", None)
        return MenuItemResponse(**res_dict)

    async def _get_menu_item(
        self, db: AsyncSession, menu_id: uuid.UUID, item_id: uuid.UUID
    ) -> MenuItem:
        """Lấy menu item thuộc menu. Raise NotFoundException nếu không tìm thấy."""
        query = select(MenuItem).where(
            MenuItem.id == item_id, MenuItem.menu_id == menu_id
        )
        result = await db.execute(query)
        item = result.scalar_one_or_none()
        if not item:
            raise NotFoundException(
                message="Không tìm thấy menu item",
                error_code="MENU_ITEM_NOT_FOUND",
                details={"menu_id": str(menu_id), "item_id": str(item_id)},
            )
        return item

    async def _calculate_depth(
        self, db: AsyncSession, parent_id: Optional[uuid.UUID]
    ) -> int:
        """Tính depth dựa trên parent. Root = 1."""
        if parent_id is None:
            return 1

        query = select(MenuItem).where(MenuItem.id == parent_id)
        result = await db.execute(query)
        parent = result.scalar_one_or_none()
        if not parent:
            raise BadRequestException(
                message="Không tìm thấy menu item cha",
                error_code="PARENT_NOT_FOUND",
                details={"parent_id": str(parent_id)},
            )
        return parent.depth + 1

    async def _check_circular_reference(
        self, db: AsyncSession, item_id: uuid.UUID, new_parent_id: Optional[uuid.UUID]
    ) -> None:
        """
        Kiểm tra circular reference khi thay đổi parent_id.
        Đệ quy ngược từ new_parent_id lên root, nếu gặp item_id → reject.
        """
        if new_parent_id is None:
            return

        current_id = new_parent_id
        visited: set[uuid.UUID] = set()

        while current_id is not None:
            if current_id == item_id:
                raise BadRequestException(
                    message="Không thể di chuyển menu item vào dưới chính nó (circular reference)",
                    error_code="CIRCULAR_REFERENCE",
                    details={"item_id": str(item_id), "parent_id": str(new_parent_id)},
                )

            if current_id in visited:
                # Dữ liệu đã bị corrupt, dừng để tránh infinite loop
                logger.error(f"Circular reference detected in existing data: {current_id}")
                raise BadRequestException(
                    message="Phát hiện lỗi cấu trúc dữ liệu menu",
                    error_code="DATA_INTEGRITY_ERROR",
                )

            visited.add(current_id)

            query = select(MenuItem.parent_id).where(MenuItem.id == current_id)
            result = await db.execute(query)
            row = result.one_or_none()
            current_id = row[0] if row else None

    async def _validate_subtree_depth(
        self, db: AsyncSession, item_id: uuid.UUID, new_depth: int
    ) -> None:
        """
        Validate toàn bộ subtree không vượt quá MAX_DEPTH khi di chuyển item.
        Tính max depth trong subtree và cộng với new_depth.
        """
        max_child_depth = await self._get_max_subtree_depth(db, item_id)
        # max_child_depth là depth tương đối sâu nhất so với item hiện tại
        if new_depth + max_child_depth > MAX_DEPTH:
            raise BadRequestException(
                message=f"Di chuyển sẽ khiến cây menu vượt quá {MAX_DEPTH} cấp",
                error_code="MAX_DEPTH_EXCEEDED",
                details={
                    "new_depth": new_depth,
                    "subtree_depth": max_child_depth,
                    "max_allowed": MAX_DEPTH,
                },
            )

    async def _get_max_subtree_depth(
        self, db: AsyncSession, item_id: uuid.UUID
    ) -> int:
        """Lấy chiều sâu tương đối lớn nhất của subtree (0 nếu không có children)."""
        # Lấy tất cả items trong cùng menu để build subtree in-memory
        query = select(MenuItem.id, MenuItem.parent_id).where(
            MenuItem.menu_id == (
                select(MenuItem.menu_id).where(MenuItem.id == item_id).scalar_subquery()
            )
        )
        result = await db.execute(query)
        rows = result.all()

        # Build children map
        children_map: dict[uuid.UUID, list[uuid.UUID]] = {}
        for row_id, row_parent_id in rows:
            if row_parent_id is not None:
                children_map.setdefault(row_parent_id, []).append(row_id)

        # DFS tính max depth
        def _max_depth(node_id: uuid.UUID) -> int:
            children = children_map.get(node_id, [])
            if not children:
                return 0
            return 1 + max(_max_depth(child) for child in children)

        return _max_depth(item_id)

    async def _recalculate_subtree_depth(
        self, db: AsyncSession, item_id: uuid.UUID, new_depth: int
    ) -> None:
        """Recalculate depth cho item và toàn bộ subtree."""
        # Lấy item
        query = select(MenuItem).where(MenuItem.id == item_id)
        result = await db.execute(query)
        item = result.scalar_one_or_none()
        if not item:
            return

        old_depth = item.depth
        depth_diff = new_depth - old_depth

        if depth_diff == 0:
            return

        # Cập nhật item chính
        item.depth = new_depth
        db.add(item)

        # Cập nhật tất cả children đệ quy
        await self._update_children_depth(db, item_id, depth_diff)
        await db.flush()

    async def _update_children_depth(
        self, db: AsyncSession, parent_id: uuid.UUID, depth_diff: int
    ) -> None:
        """Đệ quy cập nhật depth cho tất cả children."""
        query = select(MenuItem).where(MenuItem.parent_id == parent_id)
        result = await db.execute(query)
        children = list(result.scalars().all())

        for child in children:
            child.depth = child.depth + depth_diff
            db.add(child)
            await self._update_children_depth(db, child.id, depth_diff)

    def _apply_translation(self, item: MenuItem, lang: str = "vi") -> MenuItem:
        """Đọc bản dịch của ngôn ngữ chỉ định và gán vào tiêu đề động title của MenuItem."""
        if not item:
            return item

        item.title = ""
        target_trans = None
        for t in getattr(item, "translations", []):
            if t.language and t.language.code == lang:
                target_trans = t
                break

        if not target_trans and lang != "vi":
            for t in getattr(item, "translations", []):
                if t.language and t.language.code == "vi":
                    target_trans = t
                    break

        if not target_trans and getattr(item, "translations", []):
            target_trans = item.translations[0]

        if target_trans:
            item.title = target_trans.title

        return item

    async def create_menu_item(
        self,
        db: AsyncSession,
        menu_id: uuid.UUID,
        data: MenuItemCreate,
        lang: str = "vi",
    ) -> MenuItem:
        """Tạo menu item mới với cấu hình đa ngôn ngữ."""
        # Validate menu tồn tại
        await self.get_menu_by_id(db, menu_id)

        # Validate parent thuộc cùng menu (nếu có)
        if data.parent_id is not None:
            await self._get_menu_item(db, menu_id, data.parent_id)

        # Validate target tồn tại và đang ACTIVE
        if data.target_type and data.target_type != MenuItemTargetType.EXTERNAL_LINK and data.target_id:
            await target_resolver.validate(db, data.target_type.value, data.target_id)

        # Tính depth
        depth = await self._calculate_depth(db, data.parent_id)
        if depth > MAX_DEPTH:
            raise BadRequestException(
                message=f"Menu item không thể vượt quá {MAX_DEPTH} cấp",
                error_code="MAX_DEPTH_EXCEEDED",
                details={"depth": depth, "max_allowed": MAX_DEPTH},
            )

        # 1. Tạo bản ghi MenuItem chính
        item_data = {
            "menu_id": menu_id,
            "parent_id": data.parent_id,
            "target_type": data.target_type,
            "target_id": data.target_id,
            "external_url": data.external_url,
            "open_in_new_tab": data.open_in_new_tab,
            "sort_order": data.sort_order,
            "is_visible": data.is_visible,
            "depth": depth
        }
        item = MenuItem(**item_data)
        db.add(item)
        await db.flush()

        # 2. Tạo các bản dịch translations
        from app.modules.language.models import Language
        from app.modules.menu.models import MenuItemTranslation

        lang_res = await db.execute(select(Language))
        languages = lang_res.scalars().all()
        lang_map = {l.code: l.id for l in languages}

        for lang_code, trans_data in data.translations.items():
            lang_id = lang_map.get(lang_code)
            if not lang_id:
                continue
            translation = MenuItemTranslation(
                menu_item_id=item.id,
                language_id=lang_id,
                title=trans_data.title
            )
            db.add(translation)

        await db.flush()
        db.expire(item, ["translations"])

        # Load lại MenuItem với đầy đủ translations
        query = select(MenuItem).where(MenuItem.id == item.id).options(
            selectinload(MenuItem.translations).selectinload(MenuItemTranslation.language)
        )
        res = await db.execute(query)
        item = res.scalar_one()

        self._apply_translation(item, lang=lang)
        logger.info(f"Created menu item: {item.title} (id={item.id}, menu_id={menu_id})")
        return item

    async def get_menu_item(
        self,
        db: AsyncSession,
        menu_id: uuid.UUID,
        item_id: uuid.UUID,
        lang: str = "vi",
    ) -> MenuItemResponse:
        """Lấy chi tiết menu item (cho panel config). Resolve target_info nếu có."""
        from app.modules.menu.models import MenuItemTranslation
        query = select(MenuItem).where(MenuItem.menu_id == menu_id, MenuItem.id == item_id).options(
            selectinload(MenuItem.translations).selectinload(MenuItemTranslation.language)
        )
        res = await db.execute(query)
        item = res.scalar_one_or_none()
        if not item:
            raise NotFoundException(
                message="Không tìm thấy menu item",
                error_code="MENU_ITEM_NOT_FOUND",
                details={"item_id": str(item_id)},
            )

        resolved_info = None
        if item.target_type and item.target_type != MenuItemTargetType.EXTERNAL_LINK and item.target_id:
            resolved_info = await target_resolver.resolve(db, item.target_type.value, item.target_id, lang=lang)
        
        self._apply_translation(item, lang=lang)
        return self._to_item_response(item, target_info=resolved_info)

    async def update_menu_item(
        self,
        db: AsyncSession,
        menu_id: uuid.UUID,
        item_id: uuid.UUID,
        data: MenuItemUpdate,
        lang: str = "vi",
    ) -> MenuItem:
        """
        Cập nhật chi tiết menu item (title, target, icon...).
        Không xử lý parent_id/sort_order — dùng reorder API cho kéo thả.
        """
        # Load item kèm translations
        from app.modules.menu.models import MenuItemTranslation
        query = select(MenuItem).where(MenuItem.menu_id == menu_id, MenuItem.id == item_id).options(
            selectinload(MenuItem.translations).selectinload(MenuItemTranslation.language)
        )
        res = await db.execute(query)
        item = res.scalar_one_or_none()
        if not item:
            raise NotFoundException(
                message="Không tìm thấy menu item để cập nhật",
                error_code="MENU_ITEM_NOT_FOUND",
                details={"item_id": str(item_id)},
            )

        update_data = data.model_dump(exclude_unset=True)

        # Validate target nếu thay đổi target_type hoặc target_id
        if "target_type" in update_data or "target_id" in update_data:
            effective_type = update_data.get("target_type", item.target_type)
            effective_id = update_data.get("target_id", item.target_id)
            if effective_type and effective_type != MenuItemTargetType.EXTERNAL_LINK and effective_id:
                type_value = effective_type.value if hasattr(effective_type, 'value') else effective_type
                await target_resolver.validate(db, type_value, effective_id)

        # Apply updates cho các trường chung
        for field, value in update_data.items():
            if field != "translations":
                setattr(item, field, value)

        # Apply updates cho translations
        if "translations" in update_data and update_data["translations"]:
            from app.modules.language.models import Language
            
            lang_res = await db.execute(select(Language))
            languages = lang_res.scalars().all()
            lang_map = {l.code: l.id for l in languages}

            # Lấy các translations hiện có của item
            existing_trans = {t.language.code: t for t in item.translations if t.language}

            for lang_code, trans_data in update_data["translations"].items():
                lang_id = lang_map.get(lang_code)
                if not lang_id:
                    continue
                title_val = trans_data.get("title") if isinstance(trans_data, dict) else getattr(trans_data, "title", "")
                if lang_code in existing_trans:
                    existing_trans[lang_code].title = title_val
                    db.add(existing_trans[lang_code])
                else:
                    new_trans = MenuItemTranslation(
                        menu_item_id=item.id,
                        language_id=lang_id,
                        title=title_val
                    )
                    db.add(new_trans)

        db.add(item)
        await db.flush()
        db.expire(item, ["translations"])

        # Reload
        query = select(MenuItem).where(MenuItem.id == item.id).options(
            selectinload(MenuItem.translations).selectinload(MenuItemTranslation.language)
        )
        res = await db.execute(query)
        item = res.scalar_one()

        self._apply_translation(item, lang=lang)
        logger.info(f"Updated menu item: {item.title} (id={item.id})")
        return item

    async def delete_menu_item(
        self, db: AsyncSession, menu_id: uuid.UUID, item_id: uuid.UUID
    ) -> None:
        """Xóa menu item (cascade xóa children)."""
        item = await self._get_menu_item(db, menu_id, item_id)
        await db.delete(item)
        await db.flush()
        logger.info(f"Deleted menu item: {item.title} (id={item_id})")

    # ──────────────────────────────────────────
    # Tree & Reorder
    # ──────────────────────────────────────────

    async def _build_menu_tree(self, db: AsyncSession, menu: Menu, lang: str = "vi") -> MenuTreeResponse:
        """Build tree response từ menu object, bao gồm batch resolve target_info và đa ngôn ngữ."""
        from app.modules.menu.models import MenuItemTranslation
        query = (
            select(MenuItem)
            .where(MenuItem.menu_id == menu.id)
            .order_by(MenuItem.depth, MenuItem.sort_order)
            .options(
                selectinload(MenuItem.translations).selectinload(MenuItemTranslation.language)
            )
        )
        result = await db.execute(query)
        items = list(result.scalars().all())

        # Batch resolve target_info cho tất cả items có target (hiệu suất: 1 query per type)
        targets_to_resolve: list[tuple[str, uuid.UUID]] = []
        for item in items:
            self._apply_translation(item, lang=lang)
            if item.target_type and item.target_type != MenuItemTargetType.EXTERNAL_LINK and item.target_id:
                targets_to_resolve.append((item.target_type.value, item.target_id))

        resolved_map: dict[uuid.UUID, TargetInfo] = {}
        if targets_to_resolve:
            resolved_map = await target_resolver.batch_resolve(db, targets_to_resolve, lang=lang)

        tree_nodes = self._build_tree(items, resolved_map)

        return MenuTreeResponse(
            id=menu.id,
            name=menu.name,
            code=menu.code,
            description=menu.description,
            is_active=menu.is_active,
            items=tree_nodes,
        )

    async def get_menu_tree_by_code(self, db: AsyncSession, code: str, lang: str = "vi") -> MenuTreeResponse:
        """Lấy cây menu theo code (cho public frontend)."""
        menu = await self.get_menu_by_code(db, code)
        return await self._build_menu_tree(db, menu, lang=lang)

    async def get_menu_tree_by_id(self, db: AsyncSession, menu_id: uuid.UUID, lang: str = "vi") -> MenuTreeResponse:
        """Lấy cây menu theo ID (cho admin kéo thả)."""
        menu = await self.get_menu_by_id(db, menu_id)
        return await self._build_menu_tree(db, menu, lang=lang)

    def _build_tree(
        self,
        items: list[MenuItem],
        resolved_map: Optional[dict[uuid.UUID, TargetInfo]] = None,
    ) -> list[MenuItemTreeNode]:
        """Build tree từ flat list menu items, gắn kèm target_info đã resolve."""
        if resolved_map is None:
            resolved_map = {}

        # Map id → node
        node_map: dict[uuid.UUID, MenuItemTreeNode] = {}
        root_nodes: list[MenuItemTreeNode] = []

        for item in items:
            res_dict = build_menu_item_resolved(item)
            res_dict["target_info"] = resolved_map.get(item.target_id) if item.target_id else None
            res_dict["has_link"] = item.target_type is not None or item.external_url is not None
            res_dict["children"] = []
            node = MenuItemTreeNode(**res_dict)
            node_map[item.id] = node

        # Gắn children vào parent
        for item in items:
            node = node_map[item.id]
            if item.parent_id is not None and item.parent_id in node_map:
                node_map[item.parent_id].children.append(node)
            else:
                root_nodes.append(node)

        return root_nodes

    async def reorder_items(
        self,
        db: AsyncSession,
        menu_id: uuid.UUID,
        data: MenuItemReorderRequest,
    ) -> list[MenuItem]:
        """
        Batch update sort_order và parent_id cho kéo thả.
        Validate depth và circular reference cho toàn bộ batch.
        """
        # Validate menu tồn tại
        await self.get_menu_by_id(db, menu_id)

        # Lấy tất cả items hiện có của menu
        query = select(MenuItem).where(MenuItem.menu_id == menu_id)
        result = await db.execute(query)
        existing_items = {item.id: item for item in result.scalars().all()}

        # Validate tất cả item IDs tồn tại trong menu
        for reorder_item in data.items:
            if reorder_item.id not in existing_items:
                raise NotFoundException(
                    message="Menu item không thuộc menu này",
                    error_code="MENU_ITEM_NOT_FOUND",
                    details={
                        "item_id": str(reorder_item.id),
                        "menu_id": str(menu_id),
                    },
                )

        # Build new parent map để check circular + depth
        new_parent_map: dict[uuid.UUID, Optional[uuid.UUID]] = {}
        for reorder_item in data.items:
            new_parent_map[reorder_item.id] = reorder_item.parent_id

        # Validate: không có circular reference
        for item_id in new_parent_map:
            visited: set[uuid.UUID] = set()
            current = new_parent_map.get(item_id)
            while current is not None:
                if current == item_id:
                    raise BadRequestException(
                        message="Phát hiện circular reference trong dữ liệu reorder",
                        error_code="CIRCULAR_REFERENCE",
                        details={"item_id": str(item_id)},
                    )
                if current in visited:
                    raise BadRequestException(
                        message="Phát hiện circular reference trong dữ liệu reorder",
                        error_code="CIRCULAR_REFERENCE",
                    )
                visited.add(current)
                current = new_parent_map.get(current, existing_items.get(current, MenuItem()).parent_id if current in existing_items else None)

        # Tính depth mới cho từng item
        depth_cache: dict[uuid.UUID, int] = {}

        def calc_depth(item_id: uuid.UUID) -> int:
            if item_id in depth_cache:
                return depth_cache[item_id]

            parent_id = new_parent_map.get(item_id, existing_items[item_id].parent_id if item_id in existing_items else None)
            if parent_id is None:
                depth_cache[item_id] = 1
            else:
                depth_cache[item_id] = calc_depth(parent_id) + 1

            return depth_cache[item_id]

        # Apply updates
        updated_items: list[MenuItem] = []
        for reorder_item in data.items:
            item = existing_items[reorder_item.id]
            item.parent_id = reorder_item.parent_id
            item.sort_order = reorder_item.sort_order

            # Recalculate depth
            new_depth = calc_depth(reorder_item.id)
            if new_depth > MAX_DEPTH:
                raise BadRequestException(
                    message=f"Reorder sẽ khiến menu item vượt quá {MAX_DEPTH} cấp",
                    error_code="MAX_DEPTH_EXCEEDED",
                    details={
                        "item_id": str(reorder_item.id),
                        "depth": new_depth,
                        "max_allowed": MAX_DEPTH,
                    },
                )
            item.depth = new_depth

            db.add(item)
            updated_items.append(item)

        # Recalculate depth cho children không có trong reorder list
        for reorder_item in data.items:
            await self._recalculate_children_not_in_list(
                db, reorder_item.id, depth_cache, new_parent_map, existing_items
            )

        await db.flush()
        logger.info(f"Reordered {len(updated_items)} menu items in menu {menu_id}")
        return updated_items

    async def _recalculate_children_not_in_list(
        self,
        db: AsyncSession,
        parent_id: uuid.UUID,
        depth_cache: dict[uuid.UUID, int],
        reorder_map: dict[uuid.UUID, Optional[uuid.UUID]],
        existing_items: dict[uuid.UUID, MenuItem],
    ) -> None:
        """Recalculate depth cho children không nằm trong reorder list."""
        query = select(MenuItem).where(MenuItem.parent_id == parent_id)
        result = await db.execute(query)
        children = list(result.scalars().all())

        parent_depth = depth_cache.get(parent_id, 1)

        for child in children:
            if child.id not in reorder_map:
                new_depth = parent_depth + 1
                if new_depth > MAX_DEPTH:
                    raise BadRequestException(
                        message=f"Reorder sẽ khiến menu item con vượt quá {MAX_DEPTH} cấp",
                        error_code="MAX_DEPTH_EXCEEDED",
                        details={"item_id": str(child.id), "depth": new_depth},
                    )
                child.depth = new_depth
                depth_cache[child.id] = new_depth
                db.add(child)

                # Đệ quy cho children của child
                await self._recalculate_children_not_in_list(
                    db, child.id, depth_cache, reorder_map, existing_items
                )


menu_service = MenuService()
