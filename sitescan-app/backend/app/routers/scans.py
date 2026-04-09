"""Scan API endpoints."""

import asyncio
import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from app.config import settings
from app.database import get_db
from app.services.scanner import run_scan

router = APIRouter(prefix="/api/scans", tags=["scans"])


class ScanRequest(BaseModel):
    url: str
    email: str
    payment_intent_id: str | None = None  # None = free scan

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            v = "https://" + v
        parsed = urlparse(v)
        if not parsed.hostname:
            raise ValueError("有効なURLを入力してください")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v or "." not in v:
            raise ValueError("有効なメールアドレスを入力してください")
        return v.lower().strip()


class ScanResponse(BaseModel):
    scan_id: str
    status: str
    message: str


@router.post("", response_model=ScanResponse)
async def create_scan(request: ScanRequest):
    db = await get_db()
    try:
        now = datetime.now(timezone.utc).isoformat()

        # Get or create user
        cursor = await db.execute(
            "SELECT id, free_scans_used, free_scans_reset_at, plan FROM users WHERE email = ?",
            (request.email,),
        )
        user = await cursor.fetchone()

        if user:
            user_id = user["id"]
        else:
            user_id = str(uuid.uuid4())
            await db.execute(
                "INSERT INTO users (id, email, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (user_id, request.email, now, now),
            )
            await db.commit()

        # Check free scan limit (if no payment)
        is_free = request.payment_intent_id is None

        if is_free:
            cursor = await db.execute(
                "SELECT id, free_scans_used, free_scans_reset_at FROM users WHERE id = ?",
                (user_id,),
            )
            user = await cursor.fetchone()

            # Reset monthly counter if needed
            reset_at = user["free_scans_reset_at"]
            if reset_at:
                reset_date = datetime.fromisoformat(reset_at)
                if datetime.now(timezone.utc) > reset_date:
                    await db.execute(
                        "UPDATE users SET free_scans_used = 0, free_scans_reset_at = NULL WHERE id = ?",
                        (user_id,),
                    )
                    await db.commit()

            cursor = await db.execute(
                "SELECT free_scans_used FROM users WHERE id = ?",
                (user_id,),
            )
            user = await cursor.fetchone()

            if user["free_scans_used"] >= settings.max_free_scans_per_month:
                raise HTTPException(
                    status_code=429,
                    detail=f"無料診断の月間上限（{settings.max_free_scans_per_month}回）に達しました。有料プランをご検討ください。",
                )

            # Increment free scan count
            next_month = datetime.now(timezone.utc).replace(
                day=1, hour=0, minute=0, second=0, microsecond=0,
            )
            if next_month.month == 12:
                next_month = next_month.replace(year=next_month.year + 1, month=1)
            else:
                next_month = next_month.replace(month=next_month.month + 1)

            await db.execute(
                """UPDATE users
                   SET free_scans_used = free_scans_used + 1,
                       free_scans_reset_at = COALESCE(free_scans_reset_at, ?),
                       updated_at = ?
                   WHERE id = ?""",
                (next_month.isoformat(), now, user_id),
            )

        # Check concurrent scan limit
        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM scans WHERE status = 'processing'",
        )
        row = await cursor.fetchone()
        if row["cnt"] >= settings.max_concurrent_scans:
            raise HTTPException(
                status_code=503,
                detail="現在サーバーが混み合っています。しばらくしてから再度お試しください。",
            )

        # Create scan record
        scan_id = str(uuid.uuid4())
        await db.execute(
            """INSERT INTO scans (id, user_id, url, status, payment_intent_id, created_at)
               VALUES (?, ?, ?, 'pending', ?, ?)""",
            (scan_id, user_id, request.url, request.payment_intent_id, now),
        )
        await db.commit()

        # Run scan in background
        asyncio.create_task(run_scan(scan_id))

        return ScanResponse(
            scan_id=scan_id,
            status="pending",
            message="診断を開始しました。完了次第メールでお知らせします。",
        )
    finally:
        await db.close()


@router.get("/{scan_id}")
async def get_scan(scan_id: str):
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, url, status, report_json, scores_json, error_message, created_at, completed_at FROM scans WHERE id = ?",
            (scan_id,),
        )
        scan = await cursor.fetchone()

        if not scan:
            raise HTTPException(status_code=404, detail="診断結果が見つかりません")

        import json

        result = dict(scan)
        if result["report_json"]:
            result["report"] = json.loads(result["report_json"])
            del result["report_json"]
        if result["scores_json"]:
            result["scores"] = json.loads(result["scores_json"])
            del result["scores_json"]

        return result
    finally:
        await db.close()
