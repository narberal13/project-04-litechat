"""SiteScan orchestrator — combines crawling + analysis into a single scan pipeline."""

import json
import uuid
from datetime import datetime, timezone

import aiosqlite

from app.database import get_db
from app.services.crawler import crawl_url
from app.services.analyzer import analyze_site
from app.services.notifier import send_scan_complete_email, notify_admin_error


async def run_scan(scan_id: str):
    db = await get_db()
    try:
        # Mark scan as processing
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "UPDATE scans SET status = 'processing' WHERE id = ?",
            (scan_id,),
        )
        await db.commit()

        # Get scan details
        cursor = await db.execute("SELECT * FROM scans WHERE id = ?", (scan_id,))
        scan = await cursor.fetchone()
        if not scan:
            return

        url = scan["url"]
        user_id = scan["user_id"]

        # Step 1: Crawl
        crawl_result = await crawl_url(url)

        if crawl_result.error:
            await _mark_failed(db, scan_id, f"クロール失敗: {crawl_result.error}")
            return

        # Step 2: Analyze with Claude
        try:
            analysis = await analyze_site(crawl_result)
        except Exception as e:
            await _mark_failed(db, scan_id, f"分析失敗: {str(e)}")
            await notify_admin_error(f"SiteScan分析エラー: scan_id={scan_id}, error={e}")
            return

        report = analysis["report"]
        usage = analysis["usage"]

        # Step 3: Save results
        completed_at = datetime.now(timezone.utc).isoformat()
        scores = {
            "overall": report.get("overall_score", 0),
            "sections": {
                s["name"]: s["score"] for s in report.get("sections", [])
            },
        }

        await db.execute(
            """UPDATE scans
               SET status = 'completed',
                   report_json = ?,
                   scores_json = ?,
                   api_cost_usd = ?,
                   completed_at = ?
               WHERE id = ?""",
            (
                json.dumps(report, ensure_ascii=False),
                json.dumps(scores, ensure_ascii=False),
                usage["cost_usd"],
                completed_at,
                scan_id,
            ),
        )

        # Track API usage
        await db.execute(
            """INSERT INTO api_usage (date, model, input_tokens, output_tokens, cost_usd, scan_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                usage["model"],
                usage["input_tokens"],
                usage["output_tokens"],
                usage["cost_usd"],
                scan_id,
            ),
        )
        await db.commit()

        # Step 4: Notify user
        if user_id:
            cursor = await db.execute("SELECT email FROM users WHERE id = ?", (user_id,))
            user = await cursor.fetchone()
            if user:
                await send_scan_complete_email(
                    email=user["email"],
                    url=url,
                    score=report.get("overall_score", 0),
                    scan_id=scan_id,
                )

    except Exception as e:
        await _mark_failed(db, scan_id, f"予期しないエラー: {str(e)}")
        await notify_admin_error(f"SiteScan予期しないエラー: scan_id={scan_id}, error={e}")
    finally:
        await db.close()


async def _mark_failed(db: aiosqlite.Connection, scan_id: str, error_message: str):
    await db.execute(
        "UPDATE scans SET status = 'failed', error_message = ? WHERE id = ?",
        (error_message, scan_id),
    )
    await db.commit()
