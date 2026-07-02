from datetime import datetime
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
import uuid


class AISettingsUpdateRequest(BaseModel):
    active_model: Optional[str] = Field(None, description="Tên model được chọn hoạt động chính cho Chat")
    active_embedding_model: Optional[str] = Field(None, description="Tên model được chọn hoạt động chính cho Embedding")


class AISettingsResponse(BaseModel):
    active_model: str = Field(..., description="Model chat đang hoạt động hiện tại")
    active_embedding_model: str = Field(..., description="Model embedding đang hoạt động hiện tại")
    chat_models: List[Dict[str, Any]] = Field(..., description="Danh sách các model dùng cho Chat")
    embedding_models: List[Dict[str, Any]] = Field(..., description="Danh sách các model dùng cho Embedding")
    embedding_priority_list: List[str] = Field(default=[], description="Danh sách các model thực tế được ưu tiên cấu hình cho embedding")


class AIPlaygroundRequest(BaseModel):
    model: str = Field(..., description="Tên model để chat thử nghiệm")
    prompt: str = Field(..., description="Nội dung câu hỏi gửi tới AI")
    system_prompt: Optional[str] = Field(None, description="System instruction / System prompt")
    temperature: Optional[float] = Field(0.7, description="Độ sáng tạo của model (0.0 - 1.0)")
    max_tokens: Optional[int] = Field(150, description="Giới hạn số token trả về tối đa")


class AIPlaygroundResponse(BaseModel):
    response: str = Field(..., description="Văn bản kết quả trả về từ model AI")
    latency_ms: int = Field(..., description="Thời gian phản hồi tính bằng mili-giây")
    actual_model: str = Field(..., description="Tên model thực tế đã xử lý (đã xử lý fallback nếu có)")


class AILogItem(BaseModel):
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    username: Optional[str] = None
    model: str
    prompt: str
    response: Optional[str] = None
    tokens_prompt: int
    tokens_completion: int
    cost: float
    latency_ms: int
    status: str
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AILogListResponse(BaseModel):
    total: int = Field(..., description="Tổng số log ghi nhận")
    page: int = Field(..., description="Trang hiện tại")
    page_size: int = Field(..., description="Số lượng phần tử mỗi trang")
    items: List[AILogItem] = Field(..., description="Danh sách chi tiết logs")


class AISpendItem(BaseModel):
    label: str = Field(..., description="Mốc thời gian (ngày YYYY-MM-DD, tháng YYYY-MM, hoặc năm YYYY)")
    total_cost: float = Field(..., description="Tổng chi tiêu USD trong mốc thời gian")
    total_tokens: int = Field(..., description="Tổng token tiêu thụ trong mốc thời gian")
    total_requests: int = Field(..., description="Tổng số cuộc gọi trong mốc thời gian")


class AIUserSpendItem(BaseModel):
    user_id: Optional[uuid.UUID] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    total_cost: float = Field(..., description="Tổng chi tiêu USD của người dùng")
    total_tokens: int = Field(..., description="Tổng token tiêu thụ của người dùng")
    total_requests: int = Field(..., description="Tổng số cuộc gọi của người dùng")


class AISpendResponse(BaseModel):
    time_series: List[AISpendItem] = Field(..., description="Danh sách thống kê theo thời gian")
    user_spend: List[AIUserSpendItem] = Field(..., description="Danh sách thống kê theo người dùng")


class AIEmbeddingPlaygroundRequest(BaseModel):
    model: str = Field(..., description="Tên model để test embedding")
    input: str = Field(..., description="Văn bản cần vector hóa")


class AIEmbeddingPlaygroundResponse(BaseModel):
    embedding: List[float] = Field(..., description="Vector kết quả")
    dimensions: int = Field(..., description="Số chiều vector")
    latency_ms: int = Field(..., description="Thời gian phản hồi tính bằng mili-giây")
    actual_model: str = Field(..., description="Tên model thực tế đã xử lý (đã xử lý fallback nếu có)")
