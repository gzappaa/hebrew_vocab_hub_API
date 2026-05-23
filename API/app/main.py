from collections import OrderedDict
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from config import settings
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
import logging
import time
from app.router import router
from fastapi.responses import JSONResponse
from app.queries import (
    browse_lemmas,
    search_by_meaning,
    search_by_pos,
    search_by_root,
    search_by_word,
    search_by_transcription,
    get_lemma_detail,
)



# basic logging config — reads from settings
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("hebrew_vocab_hub_log")




app = FastAPI(
    title="Hebrew Vocab Hub",
    description="Search words, roots, conjugations and more",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
)

app.include_router(router)
templates = Jinja2Templates(directory="app/templates")

@app.get("/ping-db")
async def ping_db(session: AsyncSession = Depends(get_session)):
    await session.execute(text("SELECT 1"))
    return {"status": "ok", "db": "connected"}



@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = round((time.time() - start) * 1000)
    logger.info(f"{request.method} {request.url.path} → {response.status_code} ({duration}ms)")
    return response



@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"{request.method} {request.url.path} → {exc.status_code}: {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})



@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(request, "index.html")



SEARCH_HANDLERS = {
    "meaning": search_by_meaning,
    "word": search_by_word,
    "pos": search_by_pos,
    "root": search_by_root,
    "transcription": search_by_transcription,
}


@app.get("/search")
async def search_page(
    request: Request,
    query: str = "",
    type: str = "meaning",
    deep: bool = False,
    session: AsyncSession = Depends(get_session),
):
    print(f"DEBUG type={type} query={query} deep={deep}")
    results = None
    if query:
        handler = SEARCH_HANDLERS.get(type, search_by_meaning)
        results = await handler(session, query, deep=deep)
    return templates.TemplateResponse(request, "search.html", {
        "query": query,
        "type": type,
        "deep": deep,
        "results": results,
    })




templates.env.globals['enumerate'] = enumerate

@app.get("/lemma/{lemma_id}")
async def lemma_page(
    request: Request,
    lemma_id: str,
    session: AsyncSession = Depends(get_session),
):
    lemma = await get_lemma_detail(session, lemma_id)
    if not lemma:
        raise HTTPException(status_code=404, detail="Lemma not found")

    grouped_tables = []
    for table in lemma.conj_tables:
        rows = OrderedDict()
        for cell in table.cells:
            r = cell.row_index
            if r not in rows:
                rows[r] = {"labels": cell.labels, "cells": {}}
            rows[r]["cells"][cell.cell_index] = cell

        num_cols = max(
            (max(r["cells"].keys()) for r in rows.values()),
            default=0
        ) + 1

        grouped_tables.append({
            "headers": table.headers,
            "rows": rows,
            "num_cols": num_cols,
        })

    return templates.TemplateResponse(request, "lemma.html", {
        "lemma": lemma,
        "grouped_tables": grouped_tables,
    })