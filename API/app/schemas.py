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
    lemma_url: str
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


class ConjCell(BaseModel):
    id: Optional[UUID] =  None
    row_index: Optional[int] =  None
    cell_index: Optional[int] =  None
    labels: list[str]
    hebrew: Optional[str] = None
    transcription: Optional[str] = None
    meaning: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class ConjTable(BaseModel):
    id: Optional[UUID] = None
    headers: list
    cells: list[ConjCell]
    model_config = ConfigDict(from_attributes=True)


class SentenceOut(BaseModel):
    id: Optional[UUID] = None
    sentence: Optional[str] = None
    translation: Optional[str] = None
    source: Optional[str] = None
    word: str
    model_config = ConfigDict(from_attributes=True)


class WordSourceOut(BaseModel):
    songs: int
    news: int
    youtube: int
    total: int
    model_config = ConfigDict(from_attributes=True)


class LemmaDetail(BaseModel):
    id: Optional[UUID] = None
    hebrew: Optional[str] = None
    transcription: Optional[str] = None
    part_of_speech: Optional[str] = None
    meaning: Optional[str] = None
    root: Optional[RootOut] = None
    conj_tables: list[ConjTable] = []
    sentences: list[SentenceOut] = []
    sources: Optional[WordSourceOut] = None
    model_config = ConfigDict(from_attributes=True)