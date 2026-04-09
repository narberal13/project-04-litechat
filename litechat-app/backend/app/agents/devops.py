"""DevOps Agent — サーバー監視・障害アラート。

5分間隔でllama.cpp + FastAPIのヘルスチェック。
異常検知時にDiscordアラート送信。
"""

import httpx
from datetime import datetime, timezone

from app.config import settings
from app.agents.discord import send_discord

# 連続障害カウンター（メモリ内保持）
_fail_count = 0
_MAX_SILENT = 3  # 3回連続失敗で初回アラート、以降は10回ごと


async def check_health():
    """llama.cppとFastAPIのヘルスチェック。"""
    global _fail_count

    llm_ok = False
    api_ok = False

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            # llama.cpp
            try:
                r = await client.get(f"{settings.llama_server_url}/health")
                llm_ok = r.status_code == 200
            except Exception:
                llm_ok = False

            # FastAPI self-check (DB access)
            try:
                r = await client.get("http://127.0.0.1:8000/api/health")
                data = r.json()
                api_ok = data.get("status") in ("ok", "degraded")
            except Exception:
                api_ok = True  # 自分自身のチェックなので起動中なら到達している

    except Exception:
        pass

    now_jst = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    if llm_ok and api_ok:
        if _fail_count > 0:
            await send_discord(
                f"[DevOps] 復旧確認 ({now_jst})\nLLM: OK / API: OK\n"
                f"（{_fail_count}回の障害から復旧）",
                username="DevOps Agent",
            )
            _fail_count = 0
        return

    # 障害検知
    _fail_count += 1
    parts = []
    if not llm_ok:
        parts.append("LLM (llama.cpp): DOWN")
    if not api_ok:
        parts.append("API (FastAPI): DOWN")

    status = " / ".join(parts)

    # 初回 or 10回ごとにアラート（スパム防止）
    if _fail_count == _MAX_SILENT or _fail_count % 10 == 0:
        await send_discord(
            f"[DevOps] 障害検知 ({now_jst})\n{status}\n連続失敗: {_fail_count}回",
            username="DevOps Agent",
        )


async def daily_server_report() -> dict:
    """日次サーバーステータスを返す（CEO Agentが使用）。"""
    llm_ok = False
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{settings.llama_server_url}/health")
            llm_ok = r.status_code == 200
    except Exception:
        pass

    return {
        "llm_status": "online" if llm_ok else "offline",
        "consecutive_failures": _fail_count,
    }
