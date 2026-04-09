"""きくよ Admin API — ダッシュボード。"""

import hashlib
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.database import get_db
from app.agents.ceo import daily_summary

router = APIRouter(prefix="/api/admin", tags=["admin"])
security = HTTPBasic()

ADMIN_EMAIL = "gamma.narberal@gmail.com"
ADMIN_PASSWORD_HASH = hashlib.sha256("LiteChat@Admin2026!".encode()).hexdigest()


def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    pw_hash = hashlib.sha256(credentials.password.encode()).hexdigest()
    if credentials.username != ADMIN_EMAIL or pw_hash != ADMIN_PASSWORD_HASH:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return credentials.username


@router.get("/dashboard")
async def dashboard(admin: str = Depends(verify_admin)):
    db = await get_db()
    try:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        cursor = await db.execute("SELECT COUNT(*) as cnt FROM users")
        total_users = (await cursor.fetchone())["cnt"]

        cursor = await db.execute("SELECT COUNT(*) as cnt FROM users WHERE plan = 'mainichi'")
        paid_users = (await cursor.fetchone())["cnt"]

        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM messages WHERE DATE(created_at) = ?", (today,)
        )
        messages_today = (await cursor.fetchone())["cnt"]

        cursor = await db.execute("SELECT COUNT(*) as cnt FROM messages")
        total_messages = (await cursor.fetchone())["cnt"]

        cursor = await db.execute("SELECT COUNT(*) as cnt FROM chats")
        total_chats = (await cursor.fetchone())["cnt"]

        cursor = await db.execute("SELECT COUNT(*) as cnt FROM mood_logs WHERE DATE(created_at) = ?", (today,))
        moods_today = (await cursor.fetchone())["cnt"]

        cursor = await db.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as cnt
            FROM messages
            GROUP BY DATE(created_at)
            ORDER BY date DESC LIMIT 7
        """)
        daily_messages = [dict(r) for r in await cursor.fetchall()]

        cursor = await db.execute(
            "SELECT id, email, plan, nickname, messages_today, messages_week, created_at FROM users ORDER BY created_at DESC LIMIT 20"
        )
        recent_users = [dict(r) for r in await cursor.fetchall()]

        return {
            "total_users": total_users,
            "paid_users": paid_users,
            "messages_today": messages_today,
            "total_messages": total_messages,
            "total_chats": total_chats,
            "moods_today": moods_today,
            "daily_messages": daily_messages,
            "recent_users": recent_users,
        }
    finally:
        await db.close()


@router.post("/report")
async def trigger_report(admin: str = Depends(verify_admin)):
    await daily_summary()
    return {"status": "report_sent"}


@router.get("/users")
async def list_users(admin: str = Depends(verify_admin)):
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, email, plan, nickname, messages_today, messages_week, created_at FROM users ORDER BY created_at DESC"
        )
        return [dict(r) for r in await cursor.fetchall()]
    finally:
        await db.close()
