import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class FolderCreate(BaseModel):
    """
    Request body for creating a folder.
    """
    name: str = Field(..., max_length=255, description="Tên thư mục")
    parent_id: Optional[uuid.UUID] = Field(default=None, description="ID thư mục cha (nếu có)")


class ItemRename(BaseModel):
    """
    Request body for renaming a file or folder.
    """
    name: str = Field(..., max_length=255, description="Tên mới")


class ItemMove(BaseModel):
    """
    Request body for moving a file or folder.
    """
    parent_id: Optional[uuid.UUID] = Field(default=None, description="ID thư mục cha đích")


class FileCopyRequest(BaseModel):
    """
    Request body for copying a file.
    """
    dest_parent_id: Optional[uuid.UUID] = Field(default=None, description="ID thư mục cha đích")


class MediaItemResponse(BaseModel):
    """
    Response schema for a file or folder metadata.
    """
    id: uuid.UUID
    name: str
    is_folder: bool
    parent_id: Optional[uuid.UUID] = None
    object_key: Optional[str] = None
    thumbnail_key: Optional[str] = None
    bucket: Optional[str] = None
    mime_type: Optional[str] = None
    size: Optional[int] = None
    checksum: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PresignedUrlResponse(BaseModel):
    """
    Response schema containing generated presigned URLs for client-direct S3 actions.
    """
    url: str
    fields: Optional[Dict[str, Any]] = None
    expires_in: int
