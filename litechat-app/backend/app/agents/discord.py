"""Discord Webhook — Agent通知の共通モジュール。"""

import httpx
from app.config import settings


async def send_discord(content: str, username: str = "きくよ Agent"):
    """Discord Webhookにメッセージを送信。URLが未設定なら何もしない。"""
    if not settings.discord_webhook_url:
        return

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(
                settings.discord_webhook_url,
                json={"content": content, "username": username},
            )
    except Exception:
        pass
