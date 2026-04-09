"""きくよ Agent Scheduler — 定期実行管理。

- DevOps: 5分間隔でAPIヘルスチェック
- CEO: 毎日UTC 0:00（JST 9:00）に日次レポート
- Support: 毎日UTC 3:00（JST 12:00）に非アクティブ検知
- Cleanup: 毎日UTC 15:00（JST 0:00）に7日以上前のメッセージ削除
"""

import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from app.agents.devops import check_health
from app.agents.ceo import daily_summary
from app.agents.support import check_inactive_users
from app.agents.discord import send_discord

logger = logging.getLogger("agents")

scheduler = AsyncIOScheduler()


def _run_async(coro_func):
    """APScheduler用: 非同期関数をラップ。"""
    def wrapper():
        loop = asyncio.get_event_loop()
        loop.create_task(coro_func())
    return wrapper


async def cleanup_old_messages():
    """7日以上前のメッセージを自動削除（プライバシー保護）。"""
    from app.database import get_db
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM messages WHERE created_at < datetime('now', '-7 days')"
        )
        count = (await cursor.fetchone())["cnt"]

        if count > 0:
            await db.execute(
                "DELETE FROM messages WHERE created_at < datetime('now', '-7 days')"
            )
            # 空になったチャットも削除
            await db.execute(
                "DELETE FROM chats WHERE id NOT IN (SELECT DISTINCT chat_id FROM messages)"
            )
            await db.commit()
            logger.info(f"Cleanup: deleted {count} messages older than 7 days")
            await send_discord(
                f"🧹 **自動クリーンアップ完了**\n  {count}件の古いメッセージを削除しました",
                username="System",
            )
    finally:
        await db.close()


def start_agents():
    """スケジューラーを起動。"""

    scheduler.add_job(
        _run_async(check_health),
        trigger=IntervalTrigger(minutes=5),
        id="devops_health",
        replace_existing=True,
    )

    scheduler.add_job(
        _run_async(daily_summary),
        trigger=CronTrigger(hour=0, minute=0),
        id="ceo_daily",
        replace_existing=True,
    )

    scheduler.add_job(
        _run_async(check_inactive_users),
        trigger=CronTrigger(hour=3, minute=0),
        id="support_inactive",
        replace_existing=True,
    )

    # 7日以上前のメッセージ自動削除（毎日JST 0:00 = UTC 15:00）
    scheduler.add_job(
        _run_async(cleanup_old_messages),
        trigger=CronTrigger(hour=15, minute=0),
        id="cleanup_messages",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("きくよ Agent scheduler started")

    asyncio.get_event_loop().create_task(
        send_discord(
            "🚀 **きくよ Agents 起動**\n"
            "- DevOps Agent: 5分間隔ヘルスチェック\n"
            "- Support Agent: 毎日 12:00 JST に非アクティブ検知\n"
            "- CEO Agent: 毎日 09:00 JST に日次レポート\n"
            "- Cleanup: 毎日 00:00 JST に7日以上前のメッセージ削除",
            username="System",
        )
    )


def stop_agents():
    """スケジューラーを停止。"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("きくよ Agent scheduler stopped")
