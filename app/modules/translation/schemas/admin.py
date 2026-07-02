from pydantic import BaseModel, Field
from typing import List, Dict, Any

class AISettingsUpdateRequest(BaseModel):
    active_model: str = Field(..., description="Tên model được chọn hoạt động chính")

class AISettingsResponse(BaseModel):
    active_model: str = Field(..., description="Model đang hoạt động hiện tại")
    models: List[Dict[str, Any]] = Field(..., description="Danh sách các model khả dụng")
