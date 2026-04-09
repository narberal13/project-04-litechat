"""きくよ Chat API — 傾聴AI、気分記録、週次振り返り。"""

import uuid
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.config import settings
from app.database import get_db
from app.services.llm import stream_chat
from app.services.prompt import build_system_prompt, detect_crisis, CRISIS_RESPONSE

router = APIRouter(prefix="/api/chat", tags=["chat"])

JST = timezone(timedelta(hours=9))


class SendMessageRequest(BaseModel):
    chat_id: str | None = None
    message: str
    user_id: str


class MoodLogRequest(BaseModel):
    user_id: str
    score: int  # 1-5
    note: str = ""
    tags: str = ""


@router.post("/send")
async def send_message(body: SendMessageRequest):
    db = await get_db()
    try:
        now = datetime.now(timezone.utc).isoformat()

        cursor = await db.execute(
            "SELECT id, email, plan, nickname, custom_personality, "
            "messages_today, messages_today_reset, messages_week, messages_week_reset "
            "FROM users WHERE id = ?",
            (body.user_id,),
        )
        user = await cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="ユーザーが見つかりません")

        is_admin = user["email"] == "gamma.narberal@gmail.com"

        # --- レート制限 ---
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        if user["plan"] == "free" and not is_admin:
            # 無料: 3回/日
            if user["messages_today_reset"] != today:
                await db.execute(
                    "UPDATE users SET messages_today = 0, messages_today_reset = ? WHERE id = ?",
                    (today, body.user_id),
                )
                await db.commit()
                cursor = await db.execute("SELECT * FROM users WHERE id = ?", (body.user_id,))
                user = await cursor.fetchone()

            if user["messages_today"] >= settings.free_messages_per_day:
                raise HTTPException(
                    status_code=429,
                    detail=f"今日の無料回数（{settings.free_messages_per_day}回）に達しました。「まいにちプラン」で週70回まで使えます。",
                )
        elif user["plan"] == "mainichi" and not is_admin:
            # まいにち: 70回/週
            now_jst = datetime.now(JST)
            week_start = (now_jst - timedelta(days=now_jst.weekday())).strftime("%Y-%m-%d")

            if user["messages_week_reset"] != week_start:
                await db.execute(
                    "UPDATE users SET messages_week = 0, messages_week_reset = ? WHERE id = ?",
                    (week_start, body.user_id),
                )
                await db.commit()
                cursor = await db.execute("SELECT * FROM users WHERE id = ?", (body.user_id,))
                user = await cursor.fetchone()

            if user["messages_week"] >= settings.paid_messages_per_week:
                raise HTTPException(
                    status_code=429,
                    detail=f"今週の利用回数（{settings.paid_messages_per_week}回）に達しました。来週月曜にリセットされます。",
                )

        # --- 危機検知 ---
        if detect_crisis(body.message):
            # 危機メッセージ: 即座に緊急連絡先を返す
            chat_id = body.chat_id or str(uuid.uuid4())
            if not body.chat_id:
                await db.execute(
                    "INSERT INTO chats (id, user_id, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                    (chat_id, body.user_id, "相談", now, now),
                )
            await db.execute(
                "INSERT INTO messages (chat_id, role, content, created_at) VALUES (?, 'user', ?, ?)",
                (chat_id, body.message, now),
            )
            await db.execute(
                "INSERT INTO messages (chat_id, role, content, created_at) VALUES (?, 'assistant', ?, ?)",
                (chat_id, CRISIS_RESPONSE, now),
            )
            # カウント増加
            if user["plan"] == "free":
                await db.execute(
                    "UPDATE users SET messages_today = messages_today + 1 WHERE id = ?",
                    (body.user_id,),
                )
            elif user["plan"] == "mainichi":
                await db.execute(
                    "UPDATE users SET messages_week = messages_week + 1 WHERE id = ?",
                    (body.user_id,),
                )
            await db.commit()

            async def crisis_stream():
                for char in CRISIS_RESPONSE:
                    yield f"data: {char}\n\n"
                yield "data: [DONE]\n\n"

            return StreamingResponse(
                crisis_stream(),
                media_type="text/event-stream",
                headers={"X-Chat-Id": chat_id, "Cache-Control": "no-cache"},
            )

        # --- チャット作成 or 取得 ---
        chat_id = body.chat_id
        if not chat_id:
            chat_id = str(uuid.uuid4())
            title = body.message[:20] + ("..." if len(body.message) > 20 else "")
            await db.execute(
                "INSERT INTO chats (id, user_id, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (chat_id, body.user_id, title, now, now),
            )

        # ユーザーメッセージ保存
        await db.execute(
            "INSERT INTO messages (chat_id, role, content, created_at) VALUES (?, 'user', ?, ?)",
            (chat_id, body.message, now),
        )

        # カウント増加
        if user["plan"] == "free":
            await db.execute(
                "UPDATE users SET messages_today = messages_today + 1 WHERE id = ?",
                (body.user_id,),
            )
        elif user["plan"] == "mainichi":
            await db.execute(
                "UPDATE users SET messages_week = messages_week + 1 WHERE id = ?",
                (body.user_id,),
            )

        await db.commit()

        # --- 会話履歴取得 ---
        cursor = await db.execute(
            "SELECT role, content FROM messages WHERE chat_id = ? ORDER BY created_at DESC LIMIT ?",
            (chat_id, settings.max_context_messages),
        )
        rows = await cursor.fetchall()
        history = [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

        # --- システムプロンプト構築 ---
        system_prompt = build_system_prompt(
            nickname=user["nickname"] or "",
            custom_personality=user["custom_personality"] or "",
        )

        async def generate():
            full_response = ""
            try:
                async for token in stream_chat(history, system_prompt=system_prompt):
                    full_response += token
                    yield f"data: {token}\n\n"
                yield "data: [DONE]\n\n"
            finally:
                db2 = await get_db()
                try:
                    save_time = datetime.now(timezone.utc).isoformat()
                    await db2.execute(
                        "INSERT INTO messages (chat_id, role, content, tokens, created_at) VALUES (?, 'assistant', ?, ?, ?)",
                        (chat_id, full_response, len(full_response), save_time),
                    )
                    await db2.execute(
                        "UPDATE chats SET updated_at = ? WHERE id = ?", (save_time, chat_id),
                    )
                    await db2.commit()
                finally:
                    await db2.close()

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={"X-Chat-Id": chat_id, "Cache-Control": "no-cache"},
        )
    finally:
        await db.close()


@router.get("/history/{chat_id}")
async def get_chat_history(chat_id: str):
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT role, content, created_at FROM messages WHERE chat_id = ? ORDER BY created_at",
            (chat_id,),
        )
        return {"chat_id": chat_id, "messages": [dict(r) for r in await cursor.fetchall()]}
    finally:
        await db.close()


@router.get("/list/{user_id}")
async def list_chats(user_id: str):
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, title, updated_at FROM chats WHERE user_id = ? ORDER BY updated_at DESC LIMIT 50",
            (user_id,),
        )
        return {"chats": [dict(r) for r in await cursor.fetchall()]}
    finally:
        await db.close()


@router.delete("/{chat_id}")
async def delete_chat(chat_id: str, user_id: str):
    db = await get_db()
    try:
        cursor = await db.execute("SELECT user_id FROM chats WHERE id = ?", (chat_id,))
        chat = await cursor.fetchone()
        if not chat:
            raise HTTPException(status_code=404, detail="チャットが見つかりません")
        if chat["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="権限がありません")

        await db.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
        await db.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
        await db.commit()
        return {"status": "deleted"}
    finally:
        await db.close()


# --- 気分記録 ---

@router.post("/mood")
async def record_mood(body: MoodLogRequest):
    if body.score < 1 or body.score > 5:
        raise HTTPException(status_code=400, detail="スコアは1〜5で指定してください")

    db = await get_db()
    try:
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "INSERT INTO mood_logs (user_id, score, note, tags, created_at) VALUES (?, ?, ?, ?, ?)",
            (body.user_id, body.score, body.note, body.tags, now),
        )
        await db.commit()
        return {"status": "recorded"}
    finally:
        await db.close()


@router.get("/mood/{user_id}")
async def get_mood_logs(user_id: str, days: int = 7):
    db = await get_db()
    try:
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        cursor = await db.execute(
            "SELECT score, note, tags, created_at FROM mood_logs WHERE user_id = ? AND created_at >= ? ORDER BY created_at DESC",
            (user_id, since),
        )
        return {"moods": [dict(r) for r in await cursor.fetchall()]}
    finally:
        await db.close()


# --- 週次振り返り（有料プラン限定） ---

@router.get("/retrospective/{user_id}")
async def weekly_retrospective(user_id: str):
    db = await get_db()
    try:
        cursor = await db.execute("SELECT plan FROM users WHERE id = ?", (user_id,))
        user = await cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
        if user["plan"] == "free":
            raise HTTPException(status_code=403, detail="まいにちプラン限定の機能です")

        # 過去7日間の気分ログ
        since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        cursor = await db.execute(
            "SELECT score, note, tags, created_at FROM mood_logs WHERE user_id = ? AND created_at >= ? ORDER BY created_at",
            (user_id, since),
        )
        moods = [dict(r) for r in await cursor.fetchall()]

        # 過去7日間のチャット数
        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM messages WHERE chat_id IN "
            "(SELECT id FROM chats WHERE user_id = ?) AND role = 'user' AND created_at >= ?",
            (user_id, since),
        )
        msg_count = (await cursor.fetchone())["cnt"]

        if not moods and msg_count == 0:
            return {"retrospective": "今週はまだ記録がありません。気分を記録してみてね。"}

        # 気分の統計
        if moods:
            avg_score = sum(m["score"] for m in moods) / len(moods)
            mood_emoji = ["", "😢", "😔", "😐", "😊", "😄"]
            summary_parts = [
                f"📊 今週の気分: 平均 {avg_score:.1f}/5 {mood_emoji[round(avg_score)]}",
                f"📝 気分記録: {len(moods)}回",
                f"💬 会話数: {msg_count}回",
            ]
        else:
            summary_parts = [
                "📝 気分記録: なし",
                f"💬 会話数: {msg_count}回",
            ]

        return {"retrospective": "\n".join(summary_parts), "moods": moods, "message_count": msg_count}
    finally:
        await db.close()
