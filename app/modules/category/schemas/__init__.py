from app.modules.category.schemas.common import (
    CategoryCreate,
    CategoryUpdate,
    CategoryReorderItem,
    CategoryReorderRequest,
    CategorySlugCheckResponse,
    TranslationItemResponse,
    build_seo_resolved_before_validation,
)
from app.modules.category.schemas.admin import (
    AdminCategoryResponse,
    AdminCategoryTreeNode,
)
from app.modules.category.schemas.portal import (
    PortalCategoryResponse,
    PortalCategoryTreeNode,
)

# Aliases để tương thích ngược với các file import cũ
CategoryResponse = AdminCategoryResponse
CategoryTreeNode = AdminCategoryTreeNode
