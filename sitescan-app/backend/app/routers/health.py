"""Health check and admin stats endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter

from app.database import get_db

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/stats")
async def stats():
    db = await get_db()
    try:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Today's scans
        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM scans WHERE DATE(created_at) = ?",
            (today,),
        )
        scans_today = (await cursor.fetchone())["cnt"]

        # Total scans
        cursor = await db.execute("SELECT COUNT(*) as cnt FROM scans")
        total_scans = (await cursor.fetchone())["cnt"]

        # Today's API cost
        cursor = await db.execute(
            "SELECT COALESCE(SUM(cost_usd), 0) as total FROM api_usage WHERE date = ?",
            (today,),
        )
        api_cost_today = (await cursor.fetchone())["total"]

        # Month's API cost
        month_prefix = datetime.now(timezone.utc).strftime("%Y-%m")
        cursor = await db.execute(
            "SELECT COALESCE(SUM(cost_usd), 0) as total FROM api_usage WHERE date LIKE ?",
            (f"{month_prefix}%",),
        )
        api_cost_month = (await cursor.fetchone())["total"]

        # Total users
        cursor = await db.execute("SELECT COUNT(*) as cnt FROM users")
        total_users = (await cursor.fetchone())["cnt"]

        return {
            "scans_today": scans_today,
            "total_scans": total_scans,
            "api_cost_today": round(api_cost_today, 4),
            "api_cost_month": round(api_cost_month, 4),
            "total_users": total_users,
        }
    finally:
        await db.close()
