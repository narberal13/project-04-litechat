"""ToSWatch analyzer — uses Claude Haiku to analyze ToS changes and assess impact."""

import json
from anthropic import AsyncAnthropic

from app.config import settings

ANALYSIS_PROMPT = """あなたは利用規約の変更分析の専門家です。
以下のサービスの利用規約の変更差分を分析し、フリーランス・副業者への影響を評価してください。

サービス名: {service_name}
カテゴリ: {category}

変更差分:
```
{diff_summary}
```

以下のJSON形式で出力してください。JSONのみを出力してください。

{{
  "impact_level": "high" | "medium" | "low",
  "summary": "変更内容の要約（2〜3文）",
  "key_changes": [
    {{
      "what": "何が変わったか（1文）",
      "impact": "フリーランスへの影響（1文）"
    }}
  ],
  "action_required": "ユーザーが取るべきアクション（不要ならnull）"
}}"""


async def analyze_tos_change(
    service_name: str,
    category: str,
    diff_summary: str,
) -> dict:
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": ANALYSIS_PROMPT.format(
                    service_name=service_name,
                    category=category,
                    diff_summary=diff_summary[:3000],  # Limit diff size
                ),
            }
        ],
    )

    response_text = response.content[0].text.strip()

    # Extract JSON
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        json_lines = []
        in_block = False
        for line in lines:
            if line.startswith("```") and not in_block:
                in_block = True
                continue
            elif line.startswith("```") and in_block:
                break
            elif in_block:
                json_lines.append(line)
        response_text = "\n".join(json_lines)

    analysis = json.loads(response_text)

    usage = {
        "model": "claude-haiku-4-5-20251001",
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "cost_usd": (
            response.usage.input_tokens * 0.80 / 1_000_000
            + response.usage.output_tokens * 4.0 / 1_000_000
        ),
    }

    return {"analysis": analysis, "usage": usage}
