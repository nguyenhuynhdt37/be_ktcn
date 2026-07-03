import uuid
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, model_validator
from app.core.config import settings


class PortalLanguageResponse(BaseModel):
    """
    Schema phản hồi thông tin ngôn ngữ tối giản phục vụ Public Portal.
    """
    id: uuid.UUID
    code: str
    name: str
    native_name: str
    flag_id: Optional[uuid.UUID] = None
    flag_url: Optional[str] = None
    is_default: bool

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def resolve_flag_url(cls, data: Any) -> Any:
        if not data:
            return data
        
        # 1. Nếu data là dict
        if isinstance(data, dict):
            flag = data.get("flag")
            if flag and getattr(flag, "object_key", None):
                protocol = "https" if settings.MINIO_SECURE else "http"
                data["flag_url"] = f"{protocol}://{settings.MINIO_ENDPOINT}/{getattr(flag, 'bucket', None) or settings.MINIO_BUCKET}/{getattr(flag, 'object_key', None)}"
            return data
        
        # 2. Nếu data là ORM model
        db_dict = {
            "id": getattr(data, "id", None),
            "code": getattr(data, "code", None),
            "name": getattr(data, "name", None),
            "native_name": getattr(data, "native_name", None),
            "flag_id": getattr(data, "flag_id", None),
            "is_default": getattr(data, "is_default", False),
        }
        flag = getattr(data, "flag", None)
        if flag and getattr(flag, "object_key", None):
            protocol = "https" if settings.MINIO_SECURE else "http"
            db_dict["flag_url"] = f"{protocol}://{settings.MINIO_ENDPOINT}/{getattr(flag, 'bucket', None) or settings.MINIO_BUCKET}/{getattr(flag, 'object_key', None)}"
        else:
            db_dict["flag_url"] = None
        return db_dict
