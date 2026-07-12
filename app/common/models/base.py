import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy 2.0 models.
    """

    pass


class BaseModel(Base):
    """
    Base model containing common fields like ID, created_at, and updated_at.
    """

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


# Tự động hóa chuẩn hóa đường dẫn ảnh/tệp tin trước khi lưu vào Cơ sở dữ liệu
import re
from sqlalchemy import event
from sqlalchemy.orm import Mapper

def minify_model_urls(target: any) -> None:
    """
    Tìm tất cả các trường dạng chuỗi (HTML hoặc text) có chứa link tuyệt đối đến MinIO/S3
    và tự động đổi thành đường dẫn tương đối '/api/v1/portal/media/file/' để độc lập tên miền.
    """
    try:
        from app.core.config import settings
        bucket = settings.MINIO_BUCKET
        pattern = rf"https?://[^/]+/{bucket}/"
        
        # Duyệt qua các thuộc tính của model
        for key in target.__mapper__.attrs.keys():
            value = getattr(target, key)
            if isinstance(value, str) and f"/{bucket}/" in value:
                # Thay thế link tuyệt đối bằng link tương đối chuẩn
                new_value = re.sub(pattern, "/api/v1/portal/media/file/", value)
                setattr(target, key, new_value)
    except Exception:
        # Tránh làm lỗi các tiến trình khác nếu config chưa sẵn sàng
        pass

@event.listens_for(Base, "before_insert", propagate=True)
def before_insert_listener(mapper: any, connection: any, target: any) -> None:
    minify_model_urls(target)

@event.listens_for(Base, "before_update", propagate=True)
def before_update_listener(mapper: any, connection: any, target: any) -> None:
    minify_model_urls(target)
