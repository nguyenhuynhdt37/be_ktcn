from app.modules.article.schemas.common import (
    ArticleCategoryListResponse,
    ArticleTagListResponse,
    ArticleAuthorListResponse,
    BulkActionEnum,
    BulkStatusUpdateRequest,
    BulkActionResponse,
    ArticleStatsResponse,
    ArticleAttributesUpdateRequest,
    SlugCheckResponse,
    ArticleDraftsCountResponse
)
from app.modules.article.schemas.admin import (
    ArticleCreateRequest,
    ArticleUpdateRequest,
    AdminArticleResponse
)
from app.modules.article.schemas.portal import (
    PortalArticleListResponse,
    PortalArticleResponse,
    PortalArticlePaginationResponse
)
