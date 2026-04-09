"""Agent Scheduler — APSchedulerで定期実行を管理。

- DevOps: 5分間隔でヘルスチェック
- CEO: 毎日UTC 0:00（JST 9:00）に日次レポート
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


def start_agents():
    """スケジューラーを起動。FastAPIのlifespanから呼ぶ。"""

    # DevOps: 5分間隔でヘルスチェック
    scheduler.add_job(
        _run_async(check_health),
        trigger=IntervalTrigger(minutes=5),
        id="devops_health",
        replace_existing=True,
    )

    # CEO: 毎日 UTC 0:00 (JST 9:00) に日次レポート
    scheduler.add_job(
        _run_async(daily_summary),
        trigger=CronTrigger(hour=0, minute=0),
        id="ceo_daily",
        replace_existing=True,
    )

    # Support: 毎日 UTC 3:00 (JST 12:00) に非アクティブユーザー検知
    scheduler.add_job(
        _run_async(check_inactive_users),
        trigger=CronTrigger(hour=3, minute=0),
        id="support_inactive",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Agent scheduler started (DevOps: 5min, CEO: daily 09:00 JST)")

    # 起動通知
    asyncio.get_event_loop().create_task(
        send_discord(
            "🚀 **LiteChat Agents 起動**\n"
            "- DevOps Agent: 5分間隔ヘルスチェック\n"
            "- Finance Agent: 待機中（日次レポートで起動）\n"
            "- Support Agent: 毎日 12:00 JST に非アクティブ検知\n"
            "- CEO Agent: 毎日 09:00 JST に日次レポート",
            username="System",
        )
    )


def stop_agents():
    """スケジューラーを停止。"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Agent scheduler stopped")
