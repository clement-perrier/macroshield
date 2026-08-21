import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import get_engine
from app.routers import health, macro
from app.services.scheduler import build_scheduler

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    scheduler = build_scheduler()
    scheduler.start()
    try:
        yield
    finally:
        scheduler.shutdown()
        await get_engine().dispose()


app = FastAPI(title="MacroShield Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    # Matches every Vercel deployment (production + previews) for this
    # project — the hash in the URL changes on each deploy, so a fixed
    # origin list would break on the next push.
    allow_origin_regex=r"https://macroshield-[a-z0-9]+-clement-perriers-projects\.vercel\.app",
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(macro.router)
