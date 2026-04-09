"""Chat API — handles message sending with SSE streaming."""

import asyncio
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.config import settings
from app.database import get_db
from app.services.llm import stream_chat
from app.services.modes import get_system_prompt, get_modes_list
from app.services.fallback import needs_fallback, extract_topic_keywords, lookup_with_haiku
from app.services.haiku_limit import can_use_haiku, increment_haiku_usage
from app.services.memory import extract_and_save_memories, get_user_context, get_user_memories, delete_user_memory

router = APIRouter(prefix="/api/chat", tags=["chat"])


class SendMessageRequest(BaseModel):
    chat_id: str | None = None
    message: str
    user_id: str
    mode: str = "free"


@router.get("/modes")
async def list_modes():
    return get_modes_list()


@router.post("/send")
async def send_message(body: SendMessageRequest):
    db = await get_db()
    try:
        now = datetime.now(timezone.utc).isoformat()

        cursor = await db.execute("SELECT id, email, plan, external_ai, messages_today, messages_today_reset FROM users WHERE id = ?", (body.user_id,))
        user = await cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Skip rate limit for admin
        is_admin = user["email"] == "gamma.narberal@gmail.com"

        # Rate limit for free users (admin bypasses)
        if user["plan"] == "free" and not is_admin:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
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
                    detail=f"Free plan limit reached ({settings.free_messages_per_day}/day). Upgrade to Lite for unlimited.",
                )

        # Create or get chat
        chat_id = body.chat_id
        if not chat_id:
            chat_id = str(uuid.uuid4())
            title = body.message[:30] + ("..." if len(body.message) > 30 else "")
            await db.execute(
                "INSERT INTO chats (id, user_id, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (chat_id, body.user_id, title, now, now),
            )

        # Save user message
        await db.execute(
            "INSERT INTO messages (chat_id, role, content, created_at) VALUES (?, 'user', ?, ?)",
            (chat_id, body.message, now),
        )

        if user["plan"] == "free":
            await db.execute(
                "UPDATE users SET messages_today = messages_today + 1 WHERE id = ?",
                (body.user_id,),
            )

        await db.commit()

        # Get history
        cursor = await db.execute(
            "SELECT role, content FROM messages WHERE chat_id = ? ORDER BY created_at DESC LIMIT ?",
            (chat_id, settings.max_context_messages),
        )
        rows = await cursor.fetchall()
        history = [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

        # Get mode system prompt + user memory
        system_prompt = get_system_prompt(body.mode)
        user_context = await get_user_context(body.user_id)
        system_prompt += user_context

        async def generate():
            full_response = ""
            try:
                # Collect full response from local LLM
                async for token in stream_chat(history, system_prompt=system_prompt):
                    full_response += token
                    yield f"data: {token}\n\n"

                # After streaming completes, check fallback ONLY if user opted in + has quota
                use_external = user["external_ai"] == 1
                if use_external and full_response and needs_fallback(full_response):
                    has_quota = await can_use_haiku(body.user_id, user["plan"])
                    if has_quota:
                        keywords = extract_topic_keywords(body.message)
                        haiku_fact = await lookup_with_haiku(keywords)
                        if haiku_fact:
                            await increment_haiku_usage(body.user_id)
                            supplement = f"\n\n（補足: {haiku_fact}）"
                            for char in supplement:
                                yield f"data: {char}\n\n"
                            full_response += supplement

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

                # Extract memories in background (non-blocking)
                asyncio.create_task(
                    extract_and_save_memories(body.user_id, body.message, full_response)
                )

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
            raise HTTPException(status_code=404, detail="Chat not found")
        if chat["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        await db.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
        await db.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
        await db.commit()
        return {"status": "deleted"}
    finally:
        await db.close()


@router.get("/memory/{user_id}")
async def get_memories(user_id: str):
    memories = await get_user_memories(user_id)
    return {"memories": memories}


@router.delete("/memory/{user_id}/{memory_id}")
async def remove_memory(user_id: str, memory_id: int):
    await delete_user_memory(user_id, memory_id)
    return {"status": "deleted"}
