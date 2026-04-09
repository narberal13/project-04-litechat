"""User API — registration, login, and settings."""

import hashlib
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from app.database import get_db

router = APIRouter(prefix="/api/users", tags=["users"])


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


class RegisterRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v or "." not in v:
            raise ValueError("有効なメールアドレスを入力してください")
        return v.lower().strip()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 4:
            raise ValueError("パスワードは4文字以上にしてください")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/register")
async def register(body: RegisterRequest):
    db = await get_db()
    try:
        now = datetime.now(timezone.utc).isoformat()

        cursor = await db.execute("SELECT id, plan FROM users WHERE email = ?", (body.email,))
        existing = await cursor.fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="このメールアドレスは既に登録されています。ログインしてください。")

        user_id = str(uuid.uuid4())
        pw_hash = hash_password(body.password)
        await db.execute(
            "INSERT INTO users (id, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (user_id, body.email, pw_hash, now),
        )
        await db.commit()
        return {"user_id": user_id, "email": body.email, "plan": "free", "external_ai": False}
    finally:
        await db.close()


@router.post("/login")
async def login(body: LoginRequest):
    db = await get_db()
    try:
        email = body.email.lower().strip()
        cursor = await db.execute(
            "SELECT id, email, plan, external_ai, password_hash FROM users WHERE email = ?",
            (email,),
        )
        user = await cursor.fetchone()

        if not user:
            raise HTTPException(status_code=401, detail="メールアドレスまたはパスワードが正しくありません")

        # Allow login without password for legacy users (password_hash is None)
        if user["password_hash"] and user["password_hash"] != hash_password(body.password):
            raise HTTPException(status_code=401, detail="メールアドレスまたはパスワードが正しくありません")

        return {
            "user_id": user["id"],
            "email": user["email"],
            "plan": user["plan"],
            "external_ai": bool(user["external_ai"]),
        }
    finally:
        await db.close()


@router.get("/{user_id}")
async def get_user(user_id: str):
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, email, plan, external_ai, messages_today, created_at FROM users WHERE id = ?",
            (user_id,),
        )
        user = await cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
        return dict(user)
    finally:
        await db.close()


class UpdateSettingsRequest(BaseModel):
    external_ai: bool


@router.post("/{user_id}/settings")
async def update_settings(user_id: str, body: UpdateSettingsRequest):
    db = await get_db()
    try:
        await db.execute(
            "UPDATE users SET external_ai = ? WHERE id = ?",
            (1 if body.external_ai else 0, user_id),
        )
        await db.commit()
        return {"external_ai": body.external_ai}
    finally:
        await db.close()
