from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.schemas import BrowseResponse
from app.queries import browse_lemmas

router = APIRouter()

@router.get("/api/lemmas", response_model=BrowseResponse)
async def browse(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 40,
    session: AsyncSession = Depends(get_session),
):
    return await browse_lemmas(session, page=page, page_size=page_size)