from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import LemmaSummary, BrowseResponse
import math
from fastapi import HTTPException
import logging


logger = logging.getLogger("hebrew_vocab_hub.queries")



async def browse_lemmas(
    session: AsyncSession, page: int = 1, page_size: int = 40
) -> BrowseResponse:
    offset = (page - 1) * page_size
    count = (await session.execute(text("SELECT count(*) FROM lemmas"))).scalar()

    total_pages = (count + page_size - 1) // page_size

    logger.debug(f"browse_lemmas page={page} page_size={page_size} total={count}")


    if page > total_pages :
        raise HTTPException(
            status_code=404,
            detail=f'Page {page} does not exist, there are {total_pages} pages if the page_size is {page_size}.'
        )


    rows = (await session.execute(text("""
        SELECT l.id, l.hebrew, l.transcription, l.part_of_speech, l.meaning,
               r.display AS root_display
        FROM lemmas l
        LEFT JOIN roots r ON r.id = l.root_id
        ORDER BY l.hebrew
        LIMIT :lim OFFSET :off
    """), {"lim": page_size, "off": offset})).mappings().all()

    return BrowseResponse(
        total=count,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        results=[LemmaSummary(**r) for r in rows]
    )