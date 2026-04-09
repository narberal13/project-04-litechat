"""User API — registration and plan management."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from app.database import get_db

router = APIRouter(prefix="/api/users", tags=["users"])


class RegisterRequest(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v or "." not in v:
            raise ValueError("有効なメールアドレスを入力してください")
        return v.lower().strip()


@router.post("/register")
async def register(body: RegisterRequest):
    db = await get_db()
    try:
        now = datetime.now(timezone.utc).isoformat()

        cursor = await db.execute("SELECT id, plan FROM users WHERE email = ?", (body.email,))
        existing = await cursor.fetchone()
        if existing:
            return {"user_id": existing["id"], "plan": existing["plan"], "is_new": False}

        user_id = str(uuid.uuid4())
        await db.execute(
            "INSERT INTO users (id, email, created_at) VALUES (?, ?, ?)",
            (user_id, body.email, now),
        )
        await db.commit()
        return {"user_id": user_id, "plan": "free", "is_new": True}
    finally:
        await db.close()


@router.get("/{user_id}")
async def get_user(user_id: str):
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, email, plan, messages_today, created_at FROM users WHERE id = ?",
            (user_id,),
        )
        user = await cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
        return dict(user)
    finally:
        await db.close()
