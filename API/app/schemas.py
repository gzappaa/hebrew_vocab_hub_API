from typing import Optional
from pydantic import BaseModel, ConfigDict
from uuid import UUID

class RootOut(BaseModel):
    id: UUID
    display: str
    normalized: str
    model_config = ConfigDict(from_attributes=True)

class LemmaSummary(BaseModel):
    id: UUID
    hebrew: str
    transcription: Optional[str] = None
    part_of_speech: Optional[str] = None
    meaning: str
    root_display: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class BrowseResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    results: list[LemmaSummary]