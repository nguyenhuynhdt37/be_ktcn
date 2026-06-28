import uuid
from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator

from app.shared.seo.helper import ResolvedSEO, resolve_seo
from app.core.config import settings



def build_seo_resolved_before_validation(data: Any) -> Any:
    """Helper chuyển đổi đối tượng Category (ORM hoặc dict) để tính toán seo_resolved."""
    if not data:
        return data

    # 1. Nếu data đã là dictionary (VD khi frontend gửi request payload lên)
    if isinstance(data, dict):
        name = data.get("name")
        description = data.get("description")
        slug = data.get("slug")
        seo_title = data.get("seo_title")
        seo_description = data.get("seo_description")
        seo_keywords = data.get("seo_keywords")
        seo_canonical = data.get("seo_canonical")
        seo_robots = data.get("seo_robots")
        
        # Xử lý thumbnail url
        thumbnail_url = None
        thumbnail = data.get("thumbnail")
        if thumbnail and getattr(thumbnail, "object_key", None):
            protocol = "https" if settings.MINIO_SECURE else "http"
            thumbnail_url = f"{protocol}://{settings.MINIO_ENDPOINT}/{getattr(thumbnail, 'bucket', None) or settings.MINIO_BUCKET}/{getattr(thumbnail, 'object_key', None)}"

        # Xử lý OG Image url
        seo_og_image_url = None
        seo_og_image = data.get("seo_og_image")
        if seo_og_image and getattr(seo_og_image, "object_key", None):
            protocol = "https" if settings.MINIO_SECURE else "http"
            seo_og_image_url = f"{protocol}://{settings.MINIO_ENDPOINT}/{getattr(seo_og_image, 'bucket', None) or settings.MINIO_BUCKET}/{getattr(seo_og_image, 'object_key', None)}"

        resolved = resolve_seo(
            title=name or "",
            description=description,
            thumbnail_url=thumbnail_url,
            slug=slug,
            custom_seo_title=seo_title,
            custom_seo_description=seo_description,
            custom_seo_keywords=seo_keywords,
            custom_seo_canonical=seo_canonical,
            custom_seo_robots=seo_robots,
            custom_seo_og_image_url=seo_og_image_url
        )
        data["seo_resolved"] = resolved
        return data

    # 2. Nếu data là ORM Model Category (khi query từ DB lên)
    # Trích xuất dữ liệu ra một dict sạch để Pydantic không cố gắng kích hoạt lazy load trên relationships (ví dụ: children)
    db_dict = {
        "id": getattr(data, "id", None),
        "parent_id": getattr(data, "parent_id", None),
        "name": getattr(data, "name", None),
        "slug": getattr(data, "slug", None),
        "description": getattr(data, "description", None),
        "thumbnail_id": getattr(data, "thumbnail_id", None),
        "sort_order": getattr(data, "sort_order", 0),
        "status": getattr(data, "status", "DRAFT"),
        "is_visible": getattr(data, "is_visible", True),
        "seo_title": getattr(data, "seo_title", None),
        "seo_description": getattr(data, "seo_description", None),
        "seo_keywords": getattr(data, "seo_keywords", None),
        "seo_canonical": getattr(data, "seo_canonical", None),
        "seo_robots": getattr(data, "seo_robots", None),
        "seo_og_image_id": getattr(data, "seo_og_image_id", None),
        "created_at": getattr(data, "created_at", None),
        "updated_at": getattr(data, "updated_at", None),
        "children": [] # Ngăn chặn Pydantic truy cập data.children của SQLAlchemy
    }

    # Trích xuất URL cho ảnh đại diện và ảnh OG Image từ các relationship đã eager load
    thumbnail_url = None
    thumbnail = getattr(data, "thumbnail", None)
    if thumbnail and getattr(thumbnail, "object_key", None):
        protocol = "https" if settings.MINIO_SECURE else "http"
        thumbnail_url = f"{protocol}://{settings.MINIO_ENDPOINT}/{getattr(thumbnail, 'bucket', None) or settings.MINIO_BUCKET}/{getattr(thumbnail, 'object_key', None)}"

    seo_og_image_url = None
    seo_og_image = getattr(data, "seo_og_image", None)
    if seo_og_image and getattr(seo_og_image, "object_key", None):
        protocol = "https" if settings.MINIO_SECURE else "http"
        seo_og_image_url = f"{protocol}://{settings.MINIO_ENDPOINT}/{getattr(seo_og_image, 'bucket', None) or settings.MINIO_BUCKET}/{getattr(seo_og_image, 'object_key', None)}"

    resolved = resolve_seo(
        title=db_dict["name"] or "",
        description=db_dict["description"],
        thumbnail_url=thumbnail_url,
        slug=db_dict["slug"],
        custom_seo_title=db_dict["seo_title"],
        custom_seo_description=db_dict["seo_description"],
        custom_seo_keywords=db_dict["seo_keywords"],
        custom_seo_canonical=db_dict["seo_canonical"],
        custom_seo_robots=db_dict["seo_robots"],
        custom_seo_og_image_url=seo_og_image_url
    )

    db_dict["seo_resolved"] = resolved
    return db_dict


# ──────────────────────────────────────────────
# Category Schemas
# ──────────────────────────────────────────────

class CategoryCreate(BaseModel):
    """Request body tạo danh mục mới."""
    name: str = Field(..., max_length=255, description="Tên danh mục")
    parent_id: Optional[uuid.UUID] = Field(default=None, description="ID danh mục cha (NULL = root)")
    slug: Optional[str] = Field(
        default=None, 
        max_length=255, 
        pattern=r"^[a-z0-9-]+$", 
        description="Đường dẫn SEO (chỉ gồm chữ thường, số, dấu gạch ngang)"
    )
    description: Optional[str] = Field(default=None, description="Mô tả danh mục")
    thumbnail_id: Optional[uuid.UUID] = Field(default=None, description="ID ảnh đại diện trong Media Library")
    sort_order: int = Field(default=0, description="Thứ tự sắp xếp (10, 20, 30...)")
    status: str = Field(default="DRAFT", description="Trạng thái vòng đời (DRAFT, ACTIVE, INACTIVE)")
    is_visible: bool = Field(default=True, description="Hiển thị ngoài website")
    
    # SEO
    seo_title: Optional[str] = Field(default=None, max_length=255, description="SEO Title ghi đè")
    seo_description: Optional[str] = Field(default=None, max_length=500, description="SEO Description ghi đè")
    seo_keywords: Optional[str] = Field(default=None, max_length=255, description="SEO Keywords ghi đè")
    seo_canonical: Optional[str] = Field(default=None, max_length=255, description="Canonical URL tùy chỉnh")
    seo_robots: Optional[str] = Field(default="index, follow", max_length=50, description="Robots meta")
    seo_og_image_id: Optional[uuid.UUID] = Field(default=None, description="ID ảnh OG Image chuyên dụng cho SEO")

    @field_validator("parent_id", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: Any) -> Any:
        if v == "":
            return None
        return v


class CategoryUpdate(BaseModel):
    """Request body cập nhật danh mục."""
    name: Optional[str] = Field(default=None, max_length=255)
    parent_id: Optional[uuid.UUID] = None
    slug: Optional[str] = Field(default=None, max_length=255, pattern=r"^[a-z0-9-]+$")
    description: Optional[str] = None
    thumbnail_id: Optional[uuid.UUID] = None
    sort_order: Optional[int] = None
    status: Optional[str] = None
    is_visible: Optional[bool] = None
    
    # SEO
    seo_title: Optional[str] = Field(default=None, max_length=255)
    seo_description: Optional[str] = Field(default=None, max_length=500)
    seo_keywords: Optional[str] = Field(default=None, max_length=255)
    seo_canonical: Optional[str] = Field(default=None, max_length=255)
    seo_robots: Optional[str] = Field(default=None, max_length=50)
    seo_og_image_id: Optional[uuid.UUID] = Field(default=None)

    @field_validator("parent_id", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: Any) -> Any:
        if v == "":
            return None
        return v


class CategoryResponse(BaseModel):
    """Response thông tin phẳng của danh mục bài viết."""
    id: uuid.UUID
    parent_id: Optional[uuid.UUID] = None
    name: str
    slug: str
    description: Optional[str] = None
    thumbnail_id: Optional[uuid.UUID] = None
    sort_order: int
    status: str
    is_visible: bool
    
    # SEO (Cấu hình gốc trong DB)
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    seo_keywords: Optional[str] = None
    seo_canonical: Optional[str] = None
    seo_robots: Optional[str] = None
    seo_og_image_id: Optional[uuid.UUID] = None

    # SEO (Kết quả resolved hoàn chỉnh trả ra public)
    seo_resolved: Optional[ResolvedSEO] = None
    
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_seo_before_validation(cls, data: Any) -> Any:
        """Tính toán trước seo_resolved trước khi parse data."""
        return build_seo_resolved_before_validation(data)


# ──────────────────────────────────────────────
# Tree Schemas
# ──────────────────────────────────────────────

class CategoryTreeNode(BaseModel):
    """Node trong cây danh mục (recursive)."""
    id: uuid.UUID
    parent_id: Optional[uuid.UUID] = None
    name: str
    slug: str
    description: Optional[str] = None
    thumbnail_id: Optional[uuid.UUID] = None
    sort_order: int
    status: str
    is_visible: bool
    
    # SEO (Cấu hình gốc trong DB)
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    seo_keywords: Optional[str] = None
    seo_canonical: Optional[str] = None
    seo_robots: Optional[str] = None
    seo_og_image_id: Optional[uuid.UUID] = None

    # SEO (Kết quả resolved hoàn chỉnh)
    seo_resolved: Optional[ResolvedSEO] = None
    
    children: list["CategoryTreeNode"] = []

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_seo_before_validation(cls, data: Any) -> Any:
        """Tính toán trước seo_resolved trước khi parse tree node."""
        return build_seo_resolved_before_validation(data)


# ──────────────────────────────────────────────
# Drag & Drop Reorder Schemas
# ──────────────────────────────────────────────

class CategoryReorderItem(BaseModel):
    """Một item thay đổi vị trí kéo thả."""
    id: uuid.UUID
    parent_id: Optional[uuid.UUID] = None
    sort_order: int = Field(..., ge=0, description="Mức sắp xếp mới (10, 15, 20...)")

    @field_validator("parent_id", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: Any) -> Any:
        if v == "":
            return None
        return v


class CategoryReorderRequest(BaseModel):
    """Request batch update kéo thả cấu trúc cây danh mục."""
    items: list[CategoryReorderItem] = Field(
        ..., min_length=1, description="Danh sách các danh mục cần dịch chuyển"
    )
