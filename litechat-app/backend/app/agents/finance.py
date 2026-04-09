"""Finance Agent — ユーザー・使用量・収益の日次統計。

DBから直接集計。Stripe APIは呼ばない（Webhook経由でDB更新済み）。
"""

from datetime import datetime, timezone

from app.database import get_db


async def daily_finance_report() -> dict:
    """日次財務・ユーザー統計を返す（CEO Agentが使用）。"""
    db = await get_db()
    try:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # ユーザー数
        cursor = await db.execute("SELECT COUNT(*) as cnt FROM users")
        total_users = (await cursor.fetchone())["cnt"]

        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM users WHERE plan != 'free'"
        )
        paid_users = (await cursor.fetchone())["cnt"]

        # プラン別内訳
        cursor = await db.execute(
            "SELECT plan, COUNT(*) as cnt FROM users GROUP BY plan"
        )
        plan_breakdown = {row["plan"]: row["cnt"] for row in await cursor.fetchall()}

        # 本日のメッセージ数
        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM messages WHERE created_at >= ?",
            (today,),
        )
        messages_today = (await cursor.fetchone())["cnt"]

        # 総メッセージ数
        cursor = await db.execute("SELECT COUNT(*) as cnt FROM messages")
        total_messages = (await cursor.fetchone())["cnt"]

        # 総チャット数
        cursor = await db.execute("SELECT COUNT(*) as cnt FROM chats")
        total_chats = (await cursor.fetchone())["cnt"]

        # 本日のアクティブユーザー
        cursor = await db.execute(
            "SELECT COUNT(DISTINCT user_id) as cnt FROM chats WHERE updated_at >= ?",
            (today,),
        )
        active_today = (await cursor.fetchone())["cnt"]

        # 直近7日の新規ユーザー
        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM users WHERE created_at >= date(?, '-7 days')",
            (today,),
        )
        new_users_7d = (await cursor.fetchone())["cnt"]

        # 推定月次収益（DB上のプランから計算）
        revenue_map = {"free": 0, "lite": 300, "pro": 600}
        monthly_revenue = sum(
            revenue_map.get(plan, 0) * count
            for plan, count in plan_breakdown.items()
        )

        return {
            "date": today,
            "total_users": total_users,
            "paid_users": paid_users,
            "plan_breakdown": plan_breakdown,
            "messages_today": messages_today,
            "total_messages": total_messages,
            "total_chats": total_chats,
            "active_today": active_today,
            "new_users_7d": new_users_7d,
            "monthly_revenue_jpy": monthly_revenue,
        }
    finally:
        await db.close()
