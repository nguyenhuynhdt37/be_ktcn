from typing import Optional
from pydantic import BaseModel, ConfigDict


class DegreeTranslationResponse(BaseModel):
    name: str
    abbreviation: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
