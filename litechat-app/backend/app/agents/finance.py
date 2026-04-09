"""Finance Agent — きくよ日次統計。"""

from datetime import datetime, timezone

from app.database import get_db


async def daily_finance_report() -> dict:
    """日次財務・ユーザー統計（CEO Agent用）。"""
    db = await get_db()
    try:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        cursor = await db.execute("SELECT COUNT(*) as cnt FROM users")
        total_users = (await cursor.fetchone())["cnt"]

        cursor = await db.execute("SELECT COUNT(*) as cnt FROM users WHERE plan = 'mainichi'")
        paid_users = (await cursor.fetchone())["cnt"]

        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM messages WHERE created_at >= ?", (today,),
        )
        messages_today = (await cursor.fetchone())["cnt"]

        cursor = await db.execute("SELECT COUNT(*) as cnt FROM messages")
        total_messages = (await cursor.fetchone())["cnt"]

        cursor = await db.execute("SELECT COUNT(*) as cnt FROM chats")
        total_chats = (await cursor.fetchone())["cnt"]

        cursor = await db.execute(
            "SELECT COUNT(DISTINCT user_id) as cnt FROM chats WHERE updated_at >= ?", (today,),
        )
        active_today = (await cursor.fetchone())["cnt"]

        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM users WHERE created_at >= date(?, '-7 days')", (today,),
        )
        new_users_7d = (await cursor.fetchone())["cnt"]

        cursor = await db.execute("SELECT COUNT(*) as cnt FROM mood_logs WHERE created_at >= ?", (today,))
        moods_today = (await cursor.fetchone())["cnt"]

        monthly_revenue = paid_users * 500

        return {
            "date": today,
            "total_users": total_users,
            "paid_users": paid_users,
            "messages_today": messages_today,
            "total_messages": total_messages,
            "total_chats": total_chats,
            "active_today": active_today,
            "new_users_7d": new_users_7d,
            "moods_today": moods_today,
            "monthly_revenue_jpy": monthly_revenue,
        }
    finally:
        await db.close()
