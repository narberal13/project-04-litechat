"""Privacy-safe fallback — uses Claude Haiku for factual lookups only.
NEVER sends user conversation data. Only sends extracted topic keywords."""

import re
from anthropic import AsyncAnthropic

from app.config import settings

# Patterns that suggest the local LLM couldn't answer well
FALLBACK_PATTERNS = [
    r"わかりません", r"情報.*持っていません", r"最新.*情報.*ありません",
    r"202[0-4]年", r"学習データ", r"申し訳.*できません",
    r"定義することができません", r"認識されていません", r"情報.*ありません",
    r"確認できません", r"把握.*ていません", r"詳細.*提供.*ください",
    r"不明です", r"存じません",
    r"I don't have", r"I'm not sure", r"I cannot",
    r"as of my", r"training data", r"not available", r"don't know",
    r"確定.*いません", r"特定できません", r"現在の情報では",
    r"正確な答え.*出せません", r"最新の情報", r"公式発表",
]

FALLBACK_RE = re.compile("|".join(FALLBACK_PATTERNS), re.IGNORECASE)


def needs_fallback(response: str) -> bool:
    if len(response) < 20:
        return False
    return bool(FALLBACK_RE.search(response))


def extract_topic_keywords(user_message: str) -> str:
    """Extract only topic keywords from user message.
    Strips personal info, context, and conversational parts.
    Returns minimal keyword-only query."""

    # Remove common conversational patterns
    cleaned = re.sub(r"(教えて|ください|について|とは|って何|what is|tell me|please|answer in \w+)", "", user_message, flags=re.IGNORECASE)
    # Remove personal references
    cleaned = re.sub(r"(私|僕|俺|I |my |me )", "", cleaned, flags=re.IGNORECASE)
    # Keep only substantive words, remove filler
    cleaned = cleaned.strip()

    # Limit to 50 chars max
    if len(cleaned) > 50:
        cleaned = cleaned[:50]

    return cleaned if cleaned else user_message[:30]


async def lookup_with_haiku(topic_keywords: str) -> str | None:
    """Ask Claude Haiku a minimal factual question.
    Only sends topic keywords, NEVER user conversation data."""

    if not settings.anthropic_api_key:
        return None

    try:
        client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        response = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{
                "role": "user",
                "content": f"{topic_keywords} — 50文字以内で簡潔に事実のみ回答",
            }],
        )
        return response.content[0].text.strip()
    except Exception:
        return None
