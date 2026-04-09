"""CEO Agent — 日次サマリーレポートをDiscordに送信。

毎日JST 9:00（UTC 0:00）に実行。
DevOps + Financeの情報を集約し、判読しやすい形でDiscordに投稿。
"""

from app.agents.discord import send_discord
from app.agents.devops import daily_server_report
from app.agents.finance import daily_finance_report


async def daily_summary():
    """日次サマリーをDiscordに送信。"""
    server = await daily_server_report()
    finance = await daily_finance_report()

    plan = finance.get("plan_breakdown", {})
    plan_str = " / ".join(f"{k}: {v}人" for k, v in plan.items()) or "なし"

    llm_icon = "🟢" if server["llm_status"] == "online" else "🔴"
    fail_note = ""
    if server["consecutive_failures"] > 0:
        fail_note = f"  (連続障害: {server['consecutive_failures']}回)"

    msg = (
        f"📊 **LiteChat 日次レポート** ({finance['date']})\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"**サーバー**\n"
        f"  {llm_icon} LLM: {server['llm_status']}{fail_note}\n"
        f"\n"
        f"**ユーザー**\n"
        f"  総ユーザー: {finance['total_users']}人\n"
        f"  有料ユーザー: {finance['paid_users']}人\n"
        f"  プラン内訳: {plan_str}\n"
        f"  直近7日の新規: {finance['new_users_7d']}人\n"
        f"\n"
        f"**利用状況**\n"
        f"  本日メッセージ: {finance['messages_today']}\n"
        f"  本日アクティブ: {finance['active_today']}人\n"
        f"  総メッセージ: {finance['total_messages']}\n"
        f"  総チャット: {finance['total_chats']}\n"
        f"\n"
        f"**収益**\n"
        f"  推定月次収益: ¥{finance['monthly_revenue_jpy']:,}\n"
        f"━━━━━━━━━━━━━━━━━━"
    )

    await send_discord(msg, username="CEO Agent")
