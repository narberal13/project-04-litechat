"""きくよ LLMサービス — Claude Haiku APIでSSEストリーミング。"""

from collections.abc import AsyncIterator

import anthropic

from app.config import settings

client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)


async def stream_chat(
    messages: list[dict],
    max_tokens: int | None = None,
    system_prompt: str = "",
) -> AsyncIterator[str]:
    """Claude Haiku APIからストリーミング応答を取得。"""
    if max_tokens is None:
        max_tokens = settings.max_tokens_per_response

    async with client.messages.stream(
        model=settings.haiku_model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=messages,
    ) as stream:
        async for text in stream.text_stream:
            yield text


async def health_check() -> bool:
    """Anthropic APIの疎通確認。"""
    try:
        resp = await client.messages.create(
            model=settings.haiku_model,
            max_tokens=10,
            messages=[{"role": "user", "content": "ping"}],
        )
        return bool(resp.content)
    except Exception:
        return False
