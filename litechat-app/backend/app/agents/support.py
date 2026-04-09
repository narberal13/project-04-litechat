"""Support Agent — 顧客対応の自動化。

新規登録時のウェルカム通知、解約検知、非アクティブユーザー検知をDiscordに通知。
管理者がDiscordから状況を把握して対応判断できるようにする。
"""

from datetime import datetime, timezone

from app.database import get_db
from app.agents.discord import send_discord


async def notify_new_user(email: str, plan: str):
    """新規ユーザー登録時にDiscord通知。users.pyから直接呼ぶ。"""
    await send_discord(
        f"👤 **新規ユーザー登録**\n"
        f"  メール: {email}\n"
        f"  プラン: {plan}",
        username="Support Agent",
    )


async def notify_plan_change(email: str, old_plan: str, new_plan: str):
    """プラン変更時にDiscord通知。stripe_pay.pyから呼ぶ。"""
    if new_plan == "free":
        emoji = "📉"
        action = "ダウングレード（解約）"
    else:
        emoji = "🎉"
        action = "アップグレード"

    await send_discord(
        f"{emoji} **プラン変更: {action}**\n"
        f"  メール: {email}\n"
        f"  {old_plan} → {new_plan}",
        username="Support Agent",
    )


async def check_inactive_users():
    """7日以上メッセージのないユーザーを検知（日次実行）。"""
    db = await get_db()
    try:
        # 7日以上チャットしていない登録ユーザー（有料プランのみ対象）
        cursor = await db.execute("""
            SELECT u.email, u.plan, MAX(c.updated_at) as last_active
            FROM users u
            LEFT JOIN chats c ON u.id = c.user_id
            WHERE u.plan != 'free'
            GROUP BY u.id
            HAVING last_active < datetime('now', '-7 days')
               OR last_active IS NULL
        """)
        inactive = await cursor.fetchall()

        if inactive:
            lines = []
            for row in inactive:
                last = row["last_active"] or "未使用"
                lines.append(f"  - {row['email']} ({row['plan']}) 最終: {last}")

            await send_discord(
                f"⚠️ **非アクティブ有料ユーザー** ({len(inactive)}人)\n"
                + "\n".join(lines),
                username="Support Agent",
            )

        return len(inactive) if inactive else 0
    finally:
        await db.close()


async def daily_support_report() -> dict:
    """日次サポート統計を返す（CEO Agentが使用）。"""
    db = await get_db()
    try:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # 本日の新規登録数
        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM users WHERE created_at >= ?",
            (today,),
        )
        new_today = (await cursor.fetchone())["cnt"]

        return {
            "new_users_today": new_today,
        }
    finally:
        await db.close()
