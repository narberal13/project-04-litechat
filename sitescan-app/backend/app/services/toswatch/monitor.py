"""ToSWatch monitor — orchestrates crawling, diffing, analysis, and notifications."""

import json
from datetime import datetime, timezone

from app.database import get_db
from app.services.toswatch.crawler import fetch_tos_page, compute_diff, extract_changed_sections
from app.services.toswatch.analyzer import analyze_tos_change
from app.services.toswatch.targets import TARGETS
from app.services.notifier import notify_admin


async def init_toswatch_tables():
    """Create ToSWatch-specific tables."""
    db = await get_db()
    try:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS tos_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_id TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                text_content TEXT NOT NULL,
                fetched_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tos_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_id TEXT NOT NULL,
                diff_text TEXT NOT NULL,
                analysis_json TEXT,
                impact_level TEXT,
                api_cost_usd REAL DEFAULT 0,
                detected_at TEXT NOT NULL,
                notified INTEGER DEFAULT 0
            );

            CREATE INDEX IF NOT EXISTS idx_tos_snapshots_target
                ON tos_snapshots(target_id, fetched_at DESC);
            CREATE INDEX IF NOT EXISTS idx_tos_changes_target
                ON tos_changes(target_id, detected_at DESC);
        """)
        await db.commit()
    finally:
        await db.close()


async def run_tos_check():
    """Run a full check of all monitored ToS pages."""
    await init_toswatch_tables()

    changes_detected = []

    for target in TARGETS:
        try:
            result = await check_single_target(target)
            if result:
                changes_detected.append(result)
        except Exception as e:
            await notify_admin(
                f"ToSWatch error for {target['name']}: {e}"
            )

    if changes_detected:
        summary = "\n".join(
            f"- **{c['name']}** ({c['impact_level']}): {c['summary']}"
            for c in changes_detected
        )
        await notify_admin(
            f"ToSWatch: {len(changes_detected)}件の規約変更を検出\n{summary}"
        )

    return changes_detected


async def check_single_target(target: dict) -> dict | None:
    """Check a single target for ToS changes. Returns change info or None."""
    db = await get_db()
    try:
        # Fetch current page
        snapshot = await fetch_tos_page(target["id"], target["url"])

        if snapshot.error:
            return None

        # Get previous snapshot
        cursor = await db.execute(
            """SELECT content_hash, text_content FROM tos_snapshots
               WHERE target_id = ? ORDER BY fetched_at DESC LIMIT 1""",
            (target["id"],),
        )
        prev = await cursor.fetchone()

        # Save new snapshot
        await db.execute(
            """INSERT INTO tos_snapshots (target_id, content_hash, text_content, fetched_at)
               VALUES (?, ?, ?, ?)""",
            (target["id"], snapshot.content_hash, snapshot.text_content, snapshot.fetched_at),
        )
        await db.commit()

        # First snapshot — no comparison possible
        if not prev:
            return None

        # No change
        if prev["content_hash"] == snapshot.content_hash:
            return None

        # Change detected — compute diff
        diff_text = compute_diff(prev["text_content"], snapshot.text_content)
        if not diff_text:
            return None

        changed_sections = extract_changed_sections(diff_text)
        diff_summary = "\n".join(changed_sections[:50])  # Limit to 50 changes

        # Analyze with Claude Haiku
        try:
            result = await analyze_tos_change(
                service_name=target["name"],
                category=target["category"],
                diff_summary=diff_summary,
            )
            analysis = result["analysis"]
            api_cost = result["usage"]["cost_usd"]
        except Exception:
            analysis = {
                "impact_level": "medium",
                "summary": f"{target['name']}の利用規約に変更が検出されました。",
                "key_changes": [],
                "action_required": None,
            }
            api_cost = 0

        now = datetime.now(timezone.utc).isoformat()

        # Save change record
        await db.execute(
            """INSERT INTO tos_changes
               (target_id, diff_text, analysis_json, impact_level, api_cost_usd, detected_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                target["id"],
                diff_text,
                json.dumps(analysis, ensure_ascii=False),
                analysis.get("impact_level", "medium"),
                api_cost,
                now,
            ),
        )

        # Track API usage
        if api_cost > 0:
            await db.execute(
                """INSERT INTO api_usage (date, model, input_tokens, output_tokens, cost_usd, scan_id)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    "claude-haiku-4-5-20251001",
                    result["usage"]["input_tokens"],
                    result["usage"]["output_tokens"],
                    api_cost,
                    None,
                ),
            )

        await db.commit()

        return {
            "name": target["name"],
            "impact_level": analysis.get("impact_level", "medium"),
            "summary": analysis.get("summary", ""),
        }

    finally:
        await db.close()


async def get_recent_changes(limit: int = 20) -> list[dict]:
    """Get recent ToS changes for the dashboard."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT target_id, analysis_json, impact_level, detected_at
               FROM tos_changes ORDER BY detected_at DESC LIMIT ?""",
            (limit,),
        )
        rows = await cursor.fetchall()
        results = []
        for row in rows:
            target_info = next(
                (t for t in TARGETS if t["id"] == row["target_id"]), {}
            )
            results.append({
                "target_id": row["target_id"],
                "service_name": target_info.get("name", row["target_id"]),
                "category": target_info.get("category", ""),
                "analysis": json.loads(row["analysis_json"]) if row["analysis_json"] else None,
                "impact_level": row["impact_level"],
                "detected_at": row["detected_at"],
            })
        return results
    finally:
        await db.close()


async def get_monitored_services() -> list[dict]:
    """Get list of monitored services with last check status."""
    db = await get_db()
    try:
        services = []
        for target in TARGETS:
            cursor = await db.execute(
                """SELECT fetched_at FROM tos_snapshots
                   WHERE target_id = ? ORDER BY fetched_at DESC LIMIT 1""",
                (target["id"],),
            )
            row = await cursor.fetchone()
            services.append({
                **target,
                "last_checked": row["fetched_at"] if row else None,
            })
        return services
    finally:
        await db.close()
