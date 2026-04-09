"""Notification services — email (Resend) and admin alerts (Discord)."""

import httpx

from app.config import settings


async def send_scan_complete_email(email: str, url: str, score: int, scan_id: str):
    if not settings.resend_api_key:
        return

    report_url = f"{settings.app_url}/report/{scan_id}"

    async with httpx.AsyncClient() as client:
        await client.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {settings.resend_api_key}"},
            json={
                "from": settings.from_email,
                "to": [email],
                "subject": f"SiteScan 診断完了 - スコア {score}/100",
                "html": f"""
                <h2>SiteScan 診断レポート</h2>
                <p>対象サイト: <a href="{url}">{url}</a></p>
                <p>総合スコア: <strong>{score}/100</strong></p>
                <p><a href="{report_url}" style="
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #2563eb;
                    color: white;
                    text-decoration: none;
                    border-radius: 6px;
                ">レポートを見る</a></p>
                <p style="color: #666; font-size: 12px;">
                    このメールは SiteScan から自動送信されています。
                </p>
                """,
            },
        )


async def notify_admin(message: str):
    if not settings.discord_webhook_url:
        return

    async with httpx.AsyncClient() as client:
        await client.post(
            settings.discord_webhook_url,
            json={"content": message},
        )


async def notify_admin_error(message: str):
    await notify_admin(f"🚨 **エラー**: {message}")


async def notify_admin_daily_report(report: dict):
    content = f"""📊 **SiteScan 日次レポート**
━━ SiteScan ━━
診断件数: {report.get('scans_today', 0)}件
売上: ¥{report.get('revenue_today', 0):,}
━━ コスト ━━
API: ${report.get('api_cost_today', 0):.2f}（月累計 ${report.get('api_cost_month', 0):.2f}）
━━ ユーザー ━━
新規: {report.get('new_users_today', 0)}人（累計 {report.get('total_users', 0)}人）
"""

    if report.get("warnings"):
        content += f"\n⚠️ **警告**: {', '.join(report['warnings'])}"

    await notify_admin(content)
