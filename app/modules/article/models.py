from app.common.models.base import BaseModel
from app.common.models.seo import SEOMixin

class Article(BaseModel, SEOMixin):
    """
    Model Article trống để bạn xây dựng lại từ đầu.
    """
    __tablename__ = "articles"
