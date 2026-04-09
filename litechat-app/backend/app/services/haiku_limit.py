"""Haiku usage limits per plan."""

from datetime import datetime, timezone, timedelta

from app.database import get_db

# Plan limits
HAIKU_LIMITS = {
    "free": {"type": "daily", "limit": 5},
    "lite": {"type": "weekly", "limit": 30},
    "pro": {"type": "unlimited", "limit": 0},
}


async def can_use_haiku(user_id: str, plan: str) -> bool:
    """Check if user can use Haiku based on their plan limits."""
    limits = HAIKU_LIMITS.get(plan, HAIKU_LIMITS["free"])

    if limits["type"] == "unlimited":
        return True

    db = await get_db()
    try:
        now = datetime.now(timezone.utc)
        today = now.strftime("%Y-%m-%d")
        week_start = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")

        cursor = await db.execute(
            "SELECT haiku_used_today, haiku_used_week, haiku_reset_daily, haiku_reset_weekly FROM users WHERE id = ?",
            (user_id,),
        )
        user = await cursor.fetchone()
        if not user:
            return False

        # Reset daily counter
        if user["haiku_reset_daily"] != today:
            await db.execute(
                "UPDATE users SET haiku_used_today = 0, haiku_reset_daily = ? WHERE id = ?",
                (today, user_id),
            )
            await db.commit()

        # Reset weekly counter
        if user["haiku_reset_weekly"] != week_start:
            await db.execute(
                "UPDATE users SET haiku_used_week = 0, haiku_reset_weekly = ? WHERE id = ?",
                (week_start, user_id),
            )
            await db.commit()

        # Re-fetch after resets
        cursor = await db.execute(
            "SELECT haiku_used_today, haiku_used_week FROM users WHERE id = ?",
            (user_id,),
        )
        user = await cursor.fetchone()

        if limits["type"] == "daily":
            return user["haiku_used_today"] < limits["limit"]
        elif limits["type"] == "weekly":
            return user["haiku_used_week"] < limits["limit"]

        return False
    finally:
        await db.close()


async def increment_haiku_usage(user_id: str):
    """Increment Haiku usage counters."""
    db = await get_db()
    try:
        await db.execute(
            "UPDATE users SET haiku_used_today = haiku_used_today + 1, haiku_used_week = haiku_used_week + 1 WHERE id = ?",
            (user_id,),
        )
        await db.commit()
    finally:
        await db.close()
