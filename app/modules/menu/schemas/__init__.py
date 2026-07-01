from app.modules.menu.schemas.common import (
    MenuCreate,
    MenuUpdate,
    MenuItemCreate,
    MenuItemUpdate,
    MenuItemReorderItem,
    MenuItemReorderRequest,
    safe_getattr,
    build_menu_item_resolved,
)
from app.modules.menu.schemas.admin import (
    AdminMenuResponse,
    AdminMenuItemResponse,
    AdminMenuItemTreeNode,
    AdminMenuTreeResponse,
)
from app.modules.menu.schemas.portal import (
    PortalMenuItemResponse,
    PortalMenuItemTreeNode,
    PortalMenuTreeResponse,
)

# Aliases để tương thích ngược với các file import cũ
MenuResponse = AdminMenuResponse
MenuItemResponse = AdminMenuItemResponse
MenuItemTreeNode = AdminMenuItemTreeNode
MenuTreeResponse = AdminMenuTreeResponse
