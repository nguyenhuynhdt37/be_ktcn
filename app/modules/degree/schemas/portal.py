import uuid
from typing import Optional
from pydantic import BaseModel, ConfigDict


class DegreePortalResponse(BaseModel):
    """Response phẳng (đã dịch) cho Portal Website."""
    id: uuid.UUID
    name: str
    abbreviation: Optional[str] = None
    sort_order: int

    model_config = ConfigDict(from_attributes=True)
