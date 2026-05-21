from typing import Optional
from pydantic import BaseModel, ConfigDict
from uuid import UUID

class RootOut(BaseModel):
    id: Optional[UUID] = None
    display: Optional[str] = None
    normalized: Optional[str] = None
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

class SearchHit(BaseModel):
    lemma_id: UUID
    lemma_hebrew: str
    lemma_meaning: str
    lemma_transcription: Optional[str] = None
    part_of_speech: Optional[str] = None
    root: Optional[RootOut] = None
    cell_hebrew: Optional[str] = None
    cell_transcription: Optional[str] = None
    cell_meaning: Optional[str] = None
    cell_labels: Optional[list[str]] = None
    score: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)

class SearchResponse(BaseModel):
    query: str
    type: str
    total: int
    exact: bool
    results: list[SearchHit]