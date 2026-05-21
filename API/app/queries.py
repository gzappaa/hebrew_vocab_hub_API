from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import LemmaSummary, BrowseResponse, SearchResponse, SearchHit, RootOut
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

async def search_by_meaning(
    session: AsyncSession, query: str, limit: int = 20
) -> SearchResponse:
    rows = (await session.execute(text("""
        SELECT DISTINCT ON (lemma_id)
            lemma_id,
            lemma_hebrew,
            lemma_meaning,
            part_of_speech,
            lemma_transcription,
            root_id,
            root_display,
            root_normalized
        FROM v_cell_search
        WHERE lemma_meaning ILIKE :pat
        ORDER BY lemma_id
        LIMIT :lim
    """), {"pat": f"%{query}%", "lim": limit})).mappings().all()

    hits = [_row_to_hit(r) for r in rows]
    return SearchResponse(query=query, type="meaning", total=len(hits), exact=False, results=hits)


def _row_to_hit(r) -> SearchHit:
    root = None
    if r.get("root_display") and r.get("root_normalized"):
        root = RootOut(
            id=r.get("root_id"),
            display=r["root_display"],
            normalized=r["root_normalized"],
        )
    return SearchHit(
        lemma_id=r["lemma_id"],
        lemma_hebrew=r["lemma_hebrew"],
        lemma_meaning=r["lemma_meaning"],
        lemma_transcription=r.get("lemma_transcription"),
        part_of_speech=r.get("part_of_speech"),
        root=root,
        cell_hebrew=r.get("cell_hebrew"),
        cell_transcription=r.get("cell_transcription"),
        cell_meaning=r.get("cell_meaning"),
        cell_labels=r.get("cell_labels"),
        score=r.get("score"),
    )
