from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class VisitorStats(BaseModel):
    """Thống kê lượt truy cập và người đang online."""
    online_count: int = Field(description="Số người đang trực tuyến (5 phút gần nhất)")
    total_visits: int = Field(description="Tổng lượt truy cập tích lũy")


class ArticleStats(BaseModel):
    """Thống kê bài viết theo trạng thái."""
    total: int = Field(description="Tổng số bài viết (không tính thùng rác)")
    published: int = 0
    draft: int = 0
    scheduled: int = 0
    archived: int = 0
    trash: int = Field(0, description="Số bài đã xóa mềm")
    total_views: int = Field(0, description="Tổng lượt xem tất cả bài published")


class UserStats(BaseModel):
    """Thống kê tài khoản người dùng."""
    total: int = Field(description="Tổng tài khoản (không tính đã xóa)")
    active: int = 0
    locked: int = 0
    deleted: int = 0


class ConsultationStats(BaseModel):
    """Thống kê đơn tư vấn theo trạng thái."""
    total: int = 0
    new: int = 0
    contacted: int = 0
    consulting: int = 0
    completed: int = 0
    not_qualified: int = 0


class ContentStats(BaseModel):
    """Thống kê nội dung hệ thống."""
    departments: int = 0
    categories: int = 0
    banners: int = 0
    media_count: int = Field(0, description="Tổng số file media")
    media_storage_bytes: int = Field(0, description="Tổng dung lượng lưu trữ (bytes)")


class LoginStats(BaseModel):
    """Thống kê hoạt động đăng nhập."""
    today: int = Field(0, description="Số lượt đăng nhập thành công hôm nay")
    last_7_days: int = Field(0, description="Số lượt đăng nhập thành công 7 ngày qua")
    failed_today: int = Field(0, description="Số lượt đăng nhập thất bại hôm nay")


class TopArticleItem(BaseModel):
    """Một bài viết trong danh sách top views."""
    id: str
    title: str
    view_count: int
    published_at: Optional[datetime] = None
    category_name: Optional[str] = None


class RecentActivityItem(BaseModel):
    """Một hoạt động gần đây từ audit log."""
    actor_username: str
    action: str
    target_type: str
    created_at: datetime


class DashboardResponse(BaseModel):
    """Response tổng hợp cho Admin Dashboard."""
    visitors: VisitorStats
    articles: ArticleStats
    users: UserStats
    consultations: ConsultationStats
    content: ContentStats
    logins: LoginStats
    top_articles: list[TopArticleItem]
    recent_activities: list[RecentActivityItem]
