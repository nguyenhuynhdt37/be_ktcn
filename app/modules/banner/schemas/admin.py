from pydantic import BaseModel, Field
from app.modules.banner.schemas.common import BannerResponse

class BannerPaginationResponse(BaseModel):
    items: list[BannerResponse]
    page: int = Field(..., description="Trang hiện tại (1-based)")
    page_size: int = Field(..., description="Số lượng phần tử trên mỗi trang")
    total_items: int = Field(..., description="Tổng số phần tử thỏa mãn bộ lọc")
    total_pages: int = Field(..., description="Tổng số trang")
    has_next: bool = Field(..., description="Có trang kế tiếp hay không")
    has_previous: bool = Field(..., description="Có trang trước đó hay không")
