"""LLM service — communicates with llama.cpp server (OpenAI-compatible API)."""

from collections.abc import AsyncIterator
import httpx
import json

from app.config import settings

DEFAULT_SYSTEM_PROMPT = """あなたは親切で知識豊富なAIアシスタント「LiteChat」です。
必ず日本語のみで回答してください。中国語は絶対に使わないでください。
簡潔かつ正確に答えてください。
わからないことは「わかりません」と正直に伝えてください。"""


async def stream_chat(
    messages: list[dict],
    max_tokens: int | None = None,
    system_prompt: str | None = None,
) -> AsyncIterator[str]:
    """Stream chat completion from llama.cpp server."""
    if max_tokens is None:
        max_tokens = settings.max_tokens_per_response

    prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
    full_messages = [{"role": "system", "content": prompt}] + messages

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST",
            f"{settings.llama_server_url}/v1/chat/completions",
            json={
                "messages": full_messages,
                "max_tokens": max_tokens,
                "temperature": 0.7,
                "stream": True,
            },
        ) as response:
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data = line[6:]
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    delta = chunk["choices"][0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yield content
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue


async def health_check() -> bool:
    """Check if llama.cpp server is running."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.llama_server_url}/health")
            return resp.status_code == 200
    except Exception:
        return False
