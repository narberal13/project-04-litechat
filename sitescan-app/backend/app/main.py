"""SiteScan API — main application entry point."""

import asyncio
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import scans, webhooks, health, toswatch
from app.services.toswatch.monitor import init_toswatch_tables, run_tos_check

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    await init_toswatch_tables()

    # Schedule ToSWatch daily check at 06:00 JST (21:00 UTC)
    scheduler.add_job(run_tos_check, "cron", hour=21, minute=0, id="toswatch_daily")
    scheduler.start()

    yield

    # Shutdown
    scheduler.shutdown()


app = FastAPI(
    title="SiteScan API",
    description="Webサイト自動診断＆改善レポート + 利用規約変更モニター",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scans.router)
app.include_router(webhooks.router)
app.include_router(health.router)
app.include_router(toswatch.router)
