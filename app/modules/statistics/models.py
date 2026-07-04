from sqlalchemy import String, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from app.common.models.base import Base

class SystemStatistics(Base):
    """
    Model lưu trữ các thông số thống kê hoặc cấu hình hệ thống dạng key-value.
    """
    __tablename__ = "system_statistics"

    key: Mapped[str] = mapped_column(String(50), primary_key=True)
    value: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
