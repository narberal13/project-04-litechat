"""User memory — extract and store facts about users for personalization.
Uses keyword-based extraction (no LLM call) for reliability."""

import re
from datetime import datetime, timezone

from app.database import get_db

MAX_MEMORIES_PER_USER = 30

# Patterns to extract memorable facts
EXTRACT_PATTERNS = [
    (r"(?:私は|僕は|俺は|I am|I'm)\s*(.+?)(?:です|だ|。|$)", "profile"),
    (r"(?:仕事は|職業は|job is|work as)\s*(.+?)(?:です|だ|。|$)", "work"),
    (r"(?:趣味は|hobby is)\s*(.+?)(?:です|だ|。|$)", "preference"),
    (r"(?:好きな|favorite|好み)\s*(.+?)(?:です|だ|。|$)", "preference"),
    (r"(?:使っている|使用|using|use)\s*(.+?)(?:です|だ|。|$)", "skill"),
    (r"(?:目標は|goal is|目指し)\s*(.+?)(?:です|だ|。|$)", "goal"),
    (r"(?:住んで|在住|live in|from)\s*(.+?)(?:です|だ|。|$)", "profile"),
    (r"(?:名前は|呼んで|call me|my name is)\s*(.+?)(?:です|だ|。|$)", "profile"),
    (r"(?:歳|才|years old|age)\s*(.+?)(?:です|だ|。|$)", "profile"),
    (r"(?:フリーランス|freelance)", "work"),
    (r"(?:エンジニア|developer|デザイナー|designer|ライター|writer|マーケター)", "work"),
    (r"(?:Python|JavaScript|React|TypeScript|Go|Rust|Java|PHP|Ruby|Swift)", "skill"),
    (r"(?:副業|side job|side hustle)", "work"),
    (r"(?:学生|student|大学)", "profile"),
]


async def extract_and_save_memories(user_id: str, user_message: str, assistant_response: str):
    """Extract memorable facts from user message using pattern matching."""
    if len(user_message) < 5:
        return

    facts = []
    text = user_message.lower()

    for pattern, category in EXTRACT_PATTERNS:
        match = re.search(pattern, user_message, re.IGNORECASE)
        if match:
            # For patterns with capture groups, use the captured text
            if match.lastindex:
                fact_text = match.group(1).strip()
                if len(fact_text) > 2 and len(fact_text) < 100:
                    facts.append((fact_text, category))
            else:
                # For patterns without capture groups, use the matched text
                fact_text = match.group(0).strip()
                if len(fact_text) > 2:
                    facts.append((fact_text, category))

    if not facts:
        return

    db = await get_db()
    try:
        now = datetime.now(timezone.utc).isoformat()

        cursor = await db.execute(
            "SELECT fact FROM user_memory WHERE user_id = ?", (user_id,)
        )
        existing = {row["fact"].lower() for row in await cursor.fetchall()}

        for fact, category in facts[:3]:
            if fact.lower() in existing:
                continue

            await db.execute(
                "INSERT INTO user_memory (user_id, fact, category, created_at) VALUES (?, ?, ?, ?)",
                (user_id, fact, category, now),
            )

        # Enforce max
        await db.execute("""
            DELETE FROM user_memory WHERE user_id = ? AND id NOT IN (
                SELECT id FROM user_memory WHERE user_id = ?
                ORDER BY created_at DESC LIMIT ?
            )
        """, (user_id, user_id, MAX_MEMORIES_PER_USER))

        await db.commit()
    finally:
        await db.close()


async def get_user_context(user_id: str) -> str:
    """Get user's stored memories as context for system prompt."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT fact, category FROM user_memory WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, MAX_MEMORIES_PER_USER),
        )
        memories = await cursor.fetchall()

        if not memories:
            return ""

        facts = "\n".join(f"- {m['fact']}（{m['category']}）" for m in memories)
        return f"\n\n【このユーザーについて記憶している情報】\n{facts}\nこの情報を自然に踏まえて回答してください。記憶していることを無理に言及する必要はありません。"
    finally:
        await db.close()


async def get_user_memories(user_id: str) -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, fact, category, created_at FROM user_memory WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        )
        return [dict(r) for r in await cursor.fetchall()]
    finally:
        await db.close()


async def delete_user_memory(user_id: str, memory_id: int):
    db = await get_db()
    try:
        await db.execute(
            "DELETE FROM user_memory WHERE id = ? AND user_id = ?", (memory_id, user_id),
        )
        await db.commit()
    finally:
        await db.close()
