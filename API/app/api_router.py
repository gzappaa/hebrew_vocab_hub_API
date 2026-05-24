from typing import Annotated
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.schemas import BrowseResponse, SearchResponse, LemmaDetail
from uuid import UUID
import logging
from app.queries import (
    browse_lemmas,
    search_by_meaning,
    search_by_pos,
    search_by_root,
    search_by_word,
    search_by_transcription,
    get_lemma_detail,
)


logger = logging.getLogger("hebrew_vocab_hub")

router = APIRouter()

@router.get("/api/browse", response_model=BrowseResponse)
async def browse(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 40,
    session: AsyncSession = Depends(get_session),
):
    logger.info(f"BROWSE page={page} size={page_size}")
    return await browse_lemmas(session, page=page, page_size=page_size)

@router.get("/api/lemmas/{lemma_id}", response_model=LemmaDetail)
async def lemma_detail(
    lemma_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    logger.info(f"LEMMA id={lemma_id}")
    result = await get_lemma_detail(session, str(lemma_id))
    if result is None:
        logger.warning(f"LEMMA NOT FOUND {lemma_id}")
        raise HTTPException(status_code=404, detail="Lemma not found")

    return result



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
    logger.info(f"SEARCH query={query} type={type} limit={limit} deep={deep}")
    handler = SEARCH_HANDLERS.get(type)
    if not handler:
        logger.warning(f"BAD TYPE {type}")
        raise HTTPException(400)

    try:
        return await handler(session, query, limit=limit, deep=deep)
    except Exception:
        logger.exception(f"SEARCH ERROR query={query} type={type}")
        raise



