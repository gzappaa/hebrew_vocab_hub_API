from typing import Annotated
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.schemas import BrowseResponse, SearchResponse
from app.queries import (
    browse_lemmas,
    search_by_meaning,
    search_by_pos,
    search_by_root,
    search_by_word,
    search_by_transcription,
)


router = APIRouter()

@router.get("/api/lemmas", response_model=BrowseResponse)
async def browse(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 40,
    session: AsyncSession = Depends(get_session),
):
    return await browse_lemmas(session, page=page, page_size=page_size)



SEARCH_HANDLERS = {
    "meaning": search_by_meaning,
    "word": search_by_word,
    "pos": search_by_pos,
    "root": search_by_root,
    "transcription": search_by_transcription,
}

@router.get("/api/search", response_model=SearchResponse)
async def search(
    query: str,
    type: str = "meaning",
    limit: int = 5000,
    deep: bool = False,
    session: AsyncSession = Depends(get_session),
):  
    
    handler = SEARCH_HANDLERS.get(type)
    if not handler:
        raise HTTPException(status_code=400, detail=f"Unknown type '{type}'")
    return await handler(session, query, limit=limit, deep=deep)



