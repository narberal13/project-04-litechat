"""きくよ — ヘルスチェック & 統計。"""

from datetime import datetime, timezone

from fastapi import APIRouter

from app.database import get_db
from app.services.llm import health_check as api_health

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health():
    api_ok = await api_health()
    return {
        "status": "ok" if api_ok else "degraded",
        "api": "ok" if api_ok else "offline",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/stats")
async def stats():
    db = await get_db()
    try:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        cursor = await db.execute("SELECT COUNT(*) as cnt FROM users")
        total_users = (await cursor.fetchone())["cnt"]

        cursor = await db.execute("SELECT COUNT(*) as cnt FROM users WHERE plan != 'free'")
        paid_users = (await cursor.fetchone())["cnt"]

        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM messages WHERE DATE(created_at) = ?", (today,)
        )
        messages_today = (await cursor.fetchone())["cnt"]

        cursor = await db.execute("SELECT COUNT(*) as cnt FROM messages")
        total_messages = (await cursor.fetchone())["cnt"]

        cursor = await db.execute("SELECT COUNT(*) as cnt FROM chats")
        total_chats = (await cursor.fetchone())["cnt"]

        return {
            "total_users": total_users,
            "paid_users": paid_users,
            "messages_today": messages_today,
            "total_messages": total_messages,
            "total_chats": total_chats,
        }
    finally:
        await db.close()
