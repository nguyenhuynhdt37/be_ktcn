import uuid
import enum
from datetime import datetime, timezone
from typing import Optional, List, Set

from sqlalchemy import select, or_, desc, asc, func
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.article.models import Article, ArticleStatus, ArticleTranslation
from app.modules.category.models import Category
from app.modules.tag.models import Tag
from app.modules.auth.models import User

# Định nghĩa SortStrategy Enum ở mức Database/Repository
class SortStrategy(str, enum.Enum):
    HOME = "HOME"          # Trang chủ: Pinned -> Publish Date
    CATEGORY = "CATEGORY"  # Danh mục: Pinned -> Featured -> Publish Date
    SEARCH = "SEARCH"      # Tìm kiếm: Featured -> Publish Date
    CUSTOM = "CUSTOM"      # Người dùng sắp xếp: Thuần túy theo field lựa chọn

# Whitelist các cột cho phép sắp xếp
SORT_COLUMNS = {
    "title": ArticleTranslation.title,
    "slug": ArticleTranslation.slug,
    "created_at": Article.created_at,
    "updated_at": Article.updated_at,
    "publish_at": Article.publish_at,
    "published_at": Article.published_at,
    "view_count": Article.view_count,
    "sort_order": Article.sort_order,
    "is_featured": Article.is_featured,
    "is_pinned": Article.is_pinned
}

class ArticleFilterParams:
    """
    Object đóng gói toàn bộ các tham số bộ lọc của bài viết.
    Hỗ trợ cả lọc theo ID (Admin) và Slug (Portal).
    """
    def __init__(
        self,
        category_slug: Optional[str] = None,
        tag_slug: Optional[str] = None,
        author_username: Optional[str] = None,
        category_id: Optional[uuid.UUID] = None,
        tag_id: Optional[uuid.UUID] = None,
        tag_ids: Optional[List[uuid.UUID]] = None,
        author_id: Optional[uuid.UUID] = None,
        is_featured: Optional[bool] = None,
        is_pinned: Optional[bool] = None,
        published_from: Optional[datetime] = None,
        published_to: Optional[datetime] = None,
        has_thumbnail: Optional[bool] = None,
        status: Optional[ArticleStatus] = None,
        deleted: bool = False
    ):
        self.category_slug = category_slug
        self.tag_slug = tag_slug
        self.author_username = author_username
        self.category_id = category_id
        self.tag_id = tag_id
        self.tag_ids = tag_ids
        self.author_id = author_id
        self.is_featured = is_featured
        self.is_pinned = is_pinned
        self.published_from = published_from
        self.published_to = published_to
        self.has_thumbnail = has_thumbnail
        self.status = status
        self.deleted = deleted


class ArticleQueryBuilder:
    """
    Stateful Query Builder dành riêng cho bảng Articles.
    Quản lý lắp ráp câu lệnh SQL trên PostgreSQL, tối ưu hóa các điều kiện lọc và JOIN.
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        self.query = select(Article)
        self._joined_relations = set()
        self.resolved_lang_id = None

    def resolve_translation(self, language_id: uuid.UUID):
        """
        Join ArticleTranslation và ghi nhận language_id để tự động
        chuyển hướng các tác vụ filter, search, sort sang bảng dịch.
        """
        self.resolved_lang_id = language_id
        self.query = self.query.join(
            ArticleTranslation,
            (ArticleTranslation.article_id == Article.id) &
            (ArticleTranslation.language_id == language_id),
            isouter=True
        )
        return self

    def public_scope(self):
        """Chỉ truy vấn các bài viết đã xuất bản, không nháp, không xóa mềm, đã đến giờ phát hành"""
        now = datetime.now(timezone.utc)
        self.query = self.query.where(
            Article.status == ArticleStatus.PUBLISHED,
            Article.is_draft.is_(False),
            Article.deleted_at.is_(None),
            Article.publish_at <= now
        )
        return self

    def admin_scope(self, deleted: bool = False):
        """Admin scope hỗ trợ xem tin nháp và tin trong thùng rác"""
        if deleted:
            self.query = self.query.where(Article.deleted_at.is_not(None))
        else:
            self.query = self.query.where(Article.deleted_at.is_(None))
        return self

    def with_portal_relations(self):
        """Eager load các quan hệ cần thiết cho Portal để tránh N+1 Query"""
        from app.modules.article.models import ArticleTranslation
        from app.modules.category.models import CategoryTranslation
        from app.modules.tag.models import TagTranslation
        self.query = self.query.options(
            joinedload(Article.category).options(
                selectinload(Category.translations).selectinload(CategoryTranslation.language)
            ),
            joinedload(Article.author).joinedload(User.avatar),
            joinedload(Article.author).load_only(User.id, User.username, User.full_name, User.avatar_url),
            selectinload(Article.tags).options(
                selectinload(Tag.translations).selectinload(TagTranslation.language)
            ),
            selectinload(Article.translations).selectinload(ArticleTranslation.language)
        )
        return self

    def _safe_join(self, relationship_prop, target_model):
        """Helper quản lý việc JOIN tránh lỗi Duplicate JOIN trong SQLAlchemy"""
        if target_model not in self._joined_relations:
            self.query = self.query.join(relationship_prop)
            self._joined_relations.add(target_model)
        return self

    def search(self, fields: list, keyword: str):
        """
        Kiến trúc tìm kiếm văn bản Generic.
        Thực hiện tìm kiếm qua toán tử ILIKE của SQL, tự động map sang ArticleTranslation nếu đã resolve_translation.
        """
        if keyword and fields:
            search_term = f"%{keyword}%"
            if self.resolved_lang_id:
                mapped_fields = []
                for field in fields:
                    col_name = field.key
                    if hasattr(ArticleTranslation, col_name):
                        mapped_fields.append(getattr(ArticleTranslation, col_name))
                    else:
                        mapped_fields.append(field)
                fields = mapped_fields

            conditions = [field.ilike(search_term) for field in fields]
            self.query = self.query.where(or_(*conditions))
        return self

    def filter(self, params: ArticleFilterParams):
        """Lọc động hỗ trợ song song cả ID (Admin) và Slug (Portal)"""
        if not params:
            return self

        # --- Slug Filters (Dành riêng cho Portal Client) ---
        if params.category_slug:
            self._safe_join(Article.category, Category)
            from app.modules.category.models import CategoryTranslation
            if self.resolved_lang_id:
                self.query = self.query.join(
                    CategoryTranslation,
                    (CategoryTranslation.category_id == Category.id) &
                    (CategoryTranslation.language_id == self.resolved_lang_id)
                )
            else:
                from app.modules.language.models import Language
                self.query = self.query.join(CategoryTranslation).join(Language)
                self.query = self.query.where(Language.code == "vi")
            self.query = self.query.where(CategoryTranslation.slug == params.category_slug)

        if params.tag_slug:
            from app.modules.tag.models import TagTranslation
            if self.resolved_lang_id:
                self.query = self.query.where(
                    Article.tags.any(
                        Tag.translations.any(
                            (TagTranslation.slug == params.tag_slug) &
                            (TagTranslation.language_id == self.resolved_lang_id)
                        )
                    )
                )
            else:
                from app.modules.language.models import Language
                self.query = self.query.where(
                    Article.tags.any(
                        Tag.translations.any(
                            (TagTranslation.slug == params.tag_slug) &
                            (Language.code == "vi")
                        )
                    )
                )

        if params.author_username:
            self._safe_join(Article.author, User)
            self.query = self.query.where(User.username == params.author_username)

        # --- ID Filters (Dành riêng cho Admin CMS) ---
        if params.category_id:
            self.query = self.query.where(Article.category_id == params.category_id)

        if params.tag_id:
            self.query = self.query.where(Article.tags.any(Tag.id == params.tag_id))

        if params.tag_ids:
            for t_id in params.tag_ids:
                self.query = self.query.where(Article.tags.any(Tag.id == t_id))

        if params.author_id:
            self.query = self.query.where(Article.author_id == params.author_id)

        # --- Common Flags & Dates ---
        if params.is_featured is not None:
            self.query = self.query.where(Article.is_featured == params.is_featured)

        if params.is_pinned is not None:
            self.query = self.query.where(Article.is_pinned == params.is_pinned)

        if params.published_from:
            self.query = self.query.where(Article.publish_at >= params.published_from)
        if params.published_to:
            self.query = self.query.where(Article.publish_at <= params.published_to)

        if params.has_thumbnail is not None:
            if params.has_thumbnail:
                self.query = self.query.where(Article.thumbnail_object_key.is_not(None))
            else:
                self.query = self.query.where(Article.thumbnail_object_key.is_(None))

        if params.status:
            self.query = self.query.where(Article.status == params.status)

        return self

    def sort(self, strategy: SortStrategy, sort_by: str = None, sort_dir: str = "desc"):
        """Sắp xếp động dựa trên Whitelist Mapping và Sort Strategy"""
        sort_column = SORT_COLUMNS.get(sort_by, Article.publish_at)
        if self.resolved_lang_id and sort_by in ["title", "slug"]:
            sort_column = getattr(ArticleTranslation, sort_by)

        direction = desc if sort_dir.lower() == "desc" else asc

        if strategy == SortStrategy.CUSTOM:
            self.query = self.query.order_by(direction(sort_column))
        elif strategy == SortStrategy.HOME:
            self.query = self.query.order_by(Article.is_pinned.desc(), direction(sort_column))
        elif strategy == SortStrategy.CATEGORY:
            self.query = self.query.order_by(Article.is_pinned.desc(), Article.is_featured.desc(), direction(sort_column))
        elif strategy == SortStrategy.SEARCH:
            self.query = self.query.order_by(Article.is_featured.desc(), direction(sort_column))

        return self

    def paginate(self, page: int, page_size: int):
        """Chuẩn hóa phân trang bảo mật (Normalization)"""
        normalized_page = max(page, 1)
        normalized_page_size = min(max(page_size, 1), 100) # Khống chế tối đa 100 tin/trang
        
        skip = (normalized_page - 1) * normalized_page_size
        self.query = self.query.offset(skip).limit(normalized_page_size)
        return self

    async def get_total_count(self) -> int:
        """Đếm tổng số bản ghi bằng phương pháp clone query & subquery tối ưu"""
        # Loại bỏ hoàn toàn order, offset và limit để tạo câu đếm sạch
        clean_query = self.query.order_by(None).offset(None).limit(None)
        
        # Bọc thành subquery để PostgreSQL tự tối ưu hóa đếm tổng số dòng
        count_stmt = select(func.count()).select_from(clean_query.subquery())
        
        result = await self.db.execute(count_stmt)
        return result.scalar() or 0

    async def execute(self) -> list[Article]:
        result = await self.db.execute(self.query)
        # Sử dụng .unique() để khử các trùng lặp đối tượng do joinedload quan hệ sinh ra
        return list(result.scalars().unique().all())
