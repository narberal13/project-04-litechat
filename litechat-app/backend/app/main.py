"""きくよ API — 傾聴AIサービス。"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import chat, users, health, admin, stripe_pay
from app.agents.scheduler import start_agents, stop_agents


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    start_agents()
    yield
    stop_agents()


app = FastAPI(
    title="きくよ API",
    description="あなたの話を聴くAI — 月¥500",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(users.router)
app.include_router(health.router)
app.include_router(admin.router)
app.include_router(stripe_pay.router)
