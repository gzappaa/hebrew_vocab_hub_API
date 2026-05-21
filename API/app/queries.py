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
    session: AsyncSession, query: str, limit: int = 1000, deep: bool = False
) -> SearchResponse:

    logger.debug(f"searching for word={query}, deep-search={deep}")

    where = """
        WHERE lemma_meaning ILIKE :pat
        OR cell_meaning ILIKE :pat
    """ if deep else """
        WHERE lemma_meaning ILIKE :pat
    """
    distinct = "" if deep else "DISTINCT ON (lemma_id)" 

    rows = (await session.execute(text(f"""
        SELECT {distinct}
            lemma_id, lemma_hebrew, lemma_meaning, part_of_speech,
            lemma_transcription, root_id, root_display, root_normalized,
            cell_hebrew, cell_transcription, cell_meaning, labels AS cell_labels
        FROM v_cell_search
        {where}
        ORDER BY lemma_id
        LIMIT :lim
    """), {"pat": f"%{query}%", "lim": limit})).mappings().all()

    hits = [_row_to_hit(r) for r in rows]
    return SearchResponse(query=query, type="meaning", total=len(hits), exact=False, results=hits)




async def search_by_word(
    session: AsyncSession, query: str, limit: int = 100, deep: bool = False
) -> SearchResponse:



    logger.debug(f"searching by word={query}")
    where = """
        WHERE cell_hebrew_plain = :q
        OR cell_hebrew_plain % :q
    """ if deep else """
        WHERE cell_hebrew_plain = :q
    """
    distinct = "" if deep else "DISTINCT ON (lemma_id)" 



    rows = (await session.execute(text(f"""
        SELECT {distinct}
            lemma_id, lemma_hebrew, lemma_meaning, part_of_speech,
            lemma_transcription, root_id, root_display, root_normalized,
            cell_hebrew, cell_transcription, cell_meaning, labels AS cell_labels
        FROM v_cell_search
        {where}
        ORDER BY lemma_id
        LIMIT :lim
    """), {"q": query, "lim": limit})).mappings().all()

    hits = [_row_to_hit(r) for r in rows]
    return SearchResponse(query=query, type="word", total=len(hits), exact=False, results=hits)



async def search_by_pos(
    session: AsyncSession, query: str, limit: int = 1000, deep: bool = False
) -> SearchResponse:
    logger.debug(f"searching by part_of_speech={query}")
    rows = (await session.execute(text("""
        SELECT DISTINCT ON (lemma_id)
            lemma_id, lemma_hebrew, lemma_meaning, part_of_speech,
            lemma_transcription, root_id, root_display, root_normalized,
            cell_hebrew, cell_transcription, cell_meaning, labels AS cell_labels
        FROM v_cell_search
        WHERE part_of_speech_plain ILIKE :pat
        ORDER BY lemma_id
        LIMIT :lim
    """), {"pat": f"%{query}%", "lim": limit})).mappings().all()

    hits = [_row_to_hit(r) for r in rows]
    return SearchResponse(query=query, type="part_of_speech", total=len(hits), exact=False, results=hits)



async def search_by_root(
    session: AsyncSession, query: str, limit: int = 1000, deep: bool = False
) -> SearchResponse:
    logger.debug(f"searching by part_of_speech={query}")
    rows = (await session.execute(text("""
        SELECT DISTINCT ON (lemma_id)
            lemma_id, lemma_hebrew, lemma_meaning, part_of_speech,
            lemma_transcription, root_id, root_display, root_normalized,
            cell_hebrew, cell_transcription, cell_meaning, labels AS cell_labels
        FROM v_cell_search
        WHERE root_normalized ILIKE :pat
        ORDER BY lemma_id
        LIMIT :lim
    """), {"pat": f"%{query}%", "lim": limit})).mappings().all()

    hits = [_row_to_hit(r) for r in rows]
    return SearchResponse(query=query, type="root", total=len(hits), exact=False, results=hits)


async def search_by_transcription(
    session: AsyncSession, query: str, limit: int = 1000, deep: bool = False
) -> SearchResponse:
    logger.debug(f"searching by transcription={query}")
    rows = (await session.execute(text("""
        WITH results AS (
            SELECT DISTINCT ON (lemma_id)
                lemma_id, lemma_hebrew, lemma_meaning, part_of_speech,
                lemma_transcription, root_id, root_display, root_normalized,
                cell_hebrew, cell_transcription, cell_meaning, labels AS cell_labels,
                similarity(cell_transcription_plain, :q) AS score
            FROM v_cell_search
            WHERE cell_transcription_plain % :q
            ORDER BY lemma_id, similarity(cell_transcription_plain, :q) DESC
        )
        SELECT * FROM results
        WHERE score = 1.0

        UNION ALL

        SELECT * FROM (
            SELECT * FROM results
            WHERE score < 1.0
            ORDER BY score DESC
            LIMIT 5
        ) fuzzy
        WHERE NOT EXISTS (SELECT 1 FROM results WHERE score = 1.0)

        ORDER BY score DESC
        LIMIT :lim
    """), {"q": query.lower(), "lim": limit})).mappings().all()

    exact = any(r["score"] == 1.0 for r in rows)
    hits = [_row_to_hit(r) for r in rows]
    return SearchResponse(query=query, type="transcription", total=len(hits), exact=exact, results=hits)






def _row_to_hit(r) -> SearchHit:
    root = None
    if r.get("root_id"):
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
