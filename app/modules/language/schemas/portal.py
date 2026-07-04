import uuid
from pydantic import BaseModel, ConfigDict


class PortalLanguageResponse(BaseModel):
    """
    Schema phản hồi thông tin ngôn ngữ tối giản phục vụ Public Portal.
    """
    id: uuid.UUID
    code: str
    name: str
    native_name: str
    is_default: bool

    model_config = ConfigDict(from_attributes=True)
