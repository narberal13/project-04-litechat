"""DevOps Agent — Haiku API疎通確認・障害アラート。

5分間隔でAnthropic API + FastAPIのヘルスチェック。
"""

import httpx
from datetime import datetime, timezone

from app.services.llm import health_check as api_health_check
from app.agents.discord import send_discord

_fail_count = 0
_MAX_SILENT = 3


async def check_health():
    """Anthropic APIとFastAPIの疎通確認。"""
    global _fail_count

    haiku_ok = await api_health_check()
    api_ok = False

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get("http://127.0.0.1:8000/api/health")
            data = r.json()
            api_ok = data.get("status") in ("ok", "degraded")
    except Exception:
        api_ok = True

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    if haiku_ok and api_ok:
        if _fail_count > 0:
            await send_discord(
                f"[DevOps] 復旧確認 ({now_str})\nHaiku API: OK / API: OK\n"
                f"（{_fail_count}回の障害から復旧）",
                username="DevOps Agent",
            )
            _fail_count = 0
        return

    _fail_count += 1
    parts = []
    if not haiku_ok:
        parts.append("Haiku API: DOWN")
    if not api_ok:
        parts.append("FastAPI: DOWN")

    status = " / ".join(parts)

    if _fail_count == _MAX_SILENT or _fail_count % 10 == 0:
        await send_discord(
            f"[DevOps] 障害検知 ({now_str})\n{status}\n連続失敗: {_fail_count}回",
            username="DevOps Agent",
        )


async def daily_server_report() -> dict:
    """日次サーバーステータス（CEO Agent用）。"""
    haiku_ok = await api_health_check()
    return {
        "api_status": "online" if haiku_ok else "offline",
        "consecutive_failures": _fail_count,
    }
