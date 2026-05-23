from fastapi import APIRouter, Request, Depends, Query, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from collections import OrderedDict
from uuid import UUID

from app.database import get_session
from app.queries import (
    browse_lemmas,
    search_by_meaning,
    search_by_word,
    search_by_pos,
    search_by_root,
    search_by_transcription,
    get_lemma_detail,
)




router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


@router.get("/")
async def root(request: Request):
    return templates.TemplateResponse(request, "index.html")



SEARCH_HANDLERS = {
    "meaning": search_by_meaning,
    "word": search_by_word,
    "pos": search_by_pos,
    "root": search_by_root,
    "transcription": search_by_transcription,
}


@router.get("/search")
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



@router.get("/lemmas/{lemma_id}")
async def lemma_page(
    request: Request,
    lemma_id: UUID,
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


@router.get("/browse")
async def browse_html(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    results = await browse_lemmas(session, page=page, page_size=page_size)

    return templates.TemplateResponse(
        request,
        "browse.html",
        {
            "data": results,
        },
    )

