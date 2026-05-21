from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from typing import Optional
import logging
from app.schemas import  (LemmaSummary,
    BrowseResponse, 
    SearchResponse, 
    SearchHit, 
    RootOut,
    ConjCell,
    ConjTable,
    SentenceOut,
    WordSourceOut,
    LemmaDetail,
)



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




async def get_lemma_detail(
    session: AsyncSession, lemma_id: str
) -> Optional[LemmaDetail]:

    logger.debug(f"fetching lemma detail for id={lemma_id}")

    # 1. Core lemma + root
    row = (await session.execute(text("""
        SELECT
            l.id, l.hebrew, l.transcription, l.part_of_speech, l.meaning,
            r.id AS root_id, r.display AS root_display, r.normalized AS root_normalized
        FROM lemmas l
        LEFT JOIN roots r ON r.id = l.root_id
        WHERE l.id = :id
    """), {"id": lemma_id})).mappings().first()
    

    if not row:
        return None

    root = None
    if row["root_id"]:
        root = RootOut(
            id=row["root_id"],
            display=row["root_display"],
            normalized=row["root_normalized"],
        )
    

    # 2. Conjugation tables
    table_rows = (await session.execute(text("""
        SELECT id, table_index, headers
        FROM conj_tables
        WHERE lemma_id = :lid
        ORDER BY table_index
    """), {"lid": lemma_id})).mappings().all()
    

    conj_tables = []
    for table in table_rows:
        cell_rows = (await session.execute(text("""
            SELECT id, labels, hebrew, transcription, meaning
            FROM conj_cells
            WHERE table_id = :tid
            ORDER BY cell_index
        """), {"tid": table["id"]})).mappings().all()
        

        conj_tables.append(ConjTable(
            table_index=table["table_index"],
            headers=table["headers"] or [],
            cells=[ConjCell(
                id=cell["id"],
                labels=cell["labels"] or [],
                hebrew=cell["hebrew"],
                transcription=cell["transcription"],
                meaning=cell["meaning"],
            ) for cell in cell_rows]
        ))
        
    # 3. Word IDs for this lemma
    word_ids = (await session.execute(text("""
        SELECT w.id
        FROM words w
        JOIN word_lemmas wl ON wl.word_id = w.id
        WHERE wl.lemma_id = :lid
    """), {"lid": lemma_id})).scalars().all()
    

    # 4. All sentences
    sentences = []
    if word_ids:
        sent_rows = (await session.execute(text("""
            SELECT s.id, s.sentence, s.translation, s.source, w.word
            FROM sentences s
            JOIN words w ON w.id = s.word_id
            WHERE s.word_id = ANY(:wids)
            ORDER BY s.id
        """), {"wids": list(word_ids)})).mappings().all()
        

        sentences = [
            SentenceOut(
                id=r["id"],
                sentence=r["sentence"],
                translation=r["translation"],
                source=r["source"],
                word=r["word"],
            ) for r in sent_rows
        ]

    # 5. Summed sources
    sources = None
    if word_ids:
        src = (await session.execute(text("""
            SELECT
                COALESCE(SUM(songs), 0)   AS songs,
                COALESCE(SUM(news), 0)    AS news,
                COALESCE(SUM(youtube), 0) AS youtube,
                COALESCE(SUM(total), 0)   AS total
            FROM word_sources
            WHERE word_id = ANY(:wids)
        """), {"wids": list(word_ids)})).mappings().first()

        if src and src["total"] > 0:
            sources = WordSourceOut(**src)

    return LemmaDetail(
        id=row["id"],
        hebrew=row["hebrew"],
        transcription=row["transcription"],
        part_of_speech=row["part_of_speech"],
        meaning=row["meaning"],
        root=root,
        conj_tables=conj_tables,
        sentences=sentences,
        sources=sources,
    )




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
        lemma_link="api/lemmas/" + str(r["lemma_id"]),
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
