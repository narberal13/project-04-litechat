"""きくよ User API — 登録、ログイン、設定、カスタム人格。"""

import asyncio
import hashlib
import random
import string
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from app.database import get_db
from app.agents.support import notify_new_user

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

        cursor = await db.execute("SELECT id FROM users WHERE email = ?", (body.email,))
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
        asyncio.create_task(notify_new_user(body.email, "free"))
        return {"user_id": user_id, "email": body.email, "plan": "free"}
    finally:
        await db.close()


@router.post("/login")
async def login(body: LoginRequest):
    db = await get_db()
    try:
        email = body.email.lower().strip()
        cursor = await db.execute(
            "SELECT id, email, plan, nickname, password_hash FROM users WHERE email = ?",
            (email,),
        )
        user = await cursor.fetchone()

        if not user:
            raise HTTPException(status_code=401, detail="メールアドレスまたはパスワードが正しくありません")

        if user["password_hash"] and user["password_hash"] != hash_password(body.password):
            raise HTTPException(status_code=401, detail="メールアドレスまたはパスワードが正しくありません")

        return {
            "user_id": user["id"],
            "email": user["email"],
            "plan": user["plan"],
            "nickname": user["nickname"] or "",
        }
    finally:
        await db.close()


@router.get("/{user_id}")
async def get_user(user_id: str):
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, email, plan, nickname, messages_today, messages_week, created_at FROM users WHERE id = ?",
            (user_id,),
        )
        user = await cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
        return dict(user)
    finally:
        await db.close()


class UpdateNicknameRequest(BaseModel):
    nickname: str


@router.post("/{user_id}/nickname")
async def update_nickname(user_id: str, body: UpdateNicknameRequest):
    db = await get_db()
    try:
        nickname = body.nickname.strip()[:20]
        await db.execute(
            "UPDATE users SET nickname = ? WHERE id = ?",
            (nickname, user_id),
        )
        await db.commit()
        return {"nickname": nickname}
    finally:
        await db.close()


class UpdatePersonalityRequest(BaseModel):
    personality: str


@router.get("/{user_id}/personality")
async def get_personality(user_id: str):
    db = await get_db()
    try:
        cursor = await db.execute("SELECT plan, custom_personality FROM users WHERE id = ?", (user_id,))
        user = await cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
        if user["plan"] == "free":
            raise HTTPException(status_code=403, detail="まいにちプラン限定の機能です")
        return {"personality": user["custom_personality"] or ""}
    finally:
        await db.close()


@router.post("/{user_id}/personality")
async def update_personality(user_id: str, body: UpdatePersonalityRequest):
    """カスタム人格設定（.md形式で保存、有料プラン限定）。"""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT plan FROM users WHERE id = ?", (user_id,))
        user = await cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
        if user["plan"] == "free":
            raise HTTPException(status_code=403, detail="まいにちプラン限定の機能です")

        # 最大2000文字に制限
        personality = body.personality.strip()[:2000]
        await db.execute(
            "UPDATE users SET custom_personality = ? WHERE id = ?",
            (personality, user_id),
        )
        await db.commit()
        return {"personality": personality}
    finally:
        await db.close()


class ResetPasswordRequest(BaseModel):
    email: str


@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest):
    db = await get_db()
    try:
        email = body.email.lower().strip()
        cursor = await db.execute("SELECT id FROM users WHERE email = ?", (email,))
        user = await cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="このメールアドレスは登録されていません")

        temp_password = "".join(random.choices(string.ascii_letters + string.digits, k=8))
        pw_hash = hash_password(temp_password)
        await db.execute("UPDATE users SET password_hash = ? WHERE email = ?", (pw_hash, email))
        await db.commit()
        return {"temporary_password": temp_password}
    finally:
        await db.close()


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 4:
            raise ValueError("新しいパスワードは4文字以上にしてください")
        return v


@router.post("/{user_id}/change-password")
async def change_password(user_id: str, body: ChangePasswordRequest):
    db = await get_db()
    try:
        cursor = await db.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
        user = await cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="ユーザーが見つかりません")

        if user["password_hash"] and user["password_hash"] != hash_password(body.old_password):
            raise HTTPException(status_code=401, detail="現在のパスワードが正しくありません")

        new_hash = hash_password(body.new_password)
        await db.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
        await db.commit()
        return {"message": "パスワードを変更しました"}
    finally:
        await db.close()
