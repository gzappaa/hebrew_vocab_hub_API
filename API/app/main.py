from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from config import settings
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
import logging
import time

# basic logging config — reads from settings
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)

logger = logging.getLogger("hebrew_vocab_hub")




app = FastAPI(
    title="Hebrew Vocab Hub",
    description="Search words, roots, conjugations and more",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
)

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

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(request, "index.html")
