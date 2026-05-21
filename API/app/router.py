from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.schemas import BrowseResponse, SearchResponse
from app.queries import browse_lemmas, search_by_meaning


router = APIRouter()

@router.get("/api/lemmas", response_model=BrowseResponse)
async def browse(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 40,
    session: AsyncSession = Depends(get_session),
):
    return await browse_lemmas(session, page=page, page_size=page_size)

from app.schemas import BrowseResponse, SearchResponse
from app.queries import browse_lemmas, search_by_meaning

SEARCH_HANDLERS = {
    "meaning": search_by_meaning,
}

@router.get("/api/search", response_model=SearchResponse)
async def search(
    query: str,
    type: str = "meaning",
    limit: int = 20,
    session: AsyncSession = Depends(get_session),
):
    handler = SEARCH_HANDLERS.get(type)
    if not handler:
        raise HTTPException(status_code=400, detail=f"Unknown type '{type}'")
    return await handler(session, query, limit=limit)