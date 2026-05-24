from fastapi import FastAPI, Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging
import time
from fastapi.templating import Jinja2Templates
from config import settings
from app.database import get_session
from app.api_router import router as api_router
from app.web_router import router as web_router
from fastapi.responses import JSONResponse
from app.errors_handler import register_exception_handlers
from logging_conf import configure_logging
import logging


logger = logging.getLogger("hebrew_vocab_hub")
configure_logging(debug=settings.DEBUG)


app = FastAPI(
    title="Hebrew Vocab Hub",
    description="Search words, roots, conjugations and more",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
)

templates = Jinja2Templates(directory="app/templates")

register_exception_handlers(app, templates)

app.include_router(api_router)
app.include_router(web_router)


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




