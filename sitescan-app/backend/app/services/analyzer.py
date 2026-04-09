"""Claude-powered site analysis — takes crawl data and produces improvement report."""

import json
from dataclasses import asdict
from anthropic import AsyncAnthropic

from app.config import settings
from app.services.crawler import CrawlResult

ANALYSIS_SYSTEM_PROMPT = """あなたはWebサイト診断の専門家です。
提供されたサイトのクロールデータを分析し、具体的で実行可能な改善レポートを生成してください。

レポートは以下のセクションで構成してください:

1. エグゼクティブサマリー（3行以内で最重要課題と最優先アクション）
2. パフォーマンス（読み込み速度、ページサイズ）
3. SEO（メタデータ、見出し構造、構造化データ）
4. コンテンツ品質（読みやすさ、CTA、情報設計）
5. モバイル対応（viewport、タップターゲット）
6. アクセシビリティ（alt属性、コントラスト）
7. 改善アクションリスト（優先度順、最大10項目）

各項目について:
- 現状の数値/状態を示す
- 🔴（要改善）🟡（注意）✅（良好）で評価
- 具体的な改善策を「→ 具体策:」の形式で提示
- 技術的すぎない、初心者にもわかる日本語で書く

出力は必ずJSON形式で返してください。"""

ANALYSIS_OUTPUT_SCHEMA = """{
  "summary": "エグゼクティブサマリー（3行以内）",
  "overall_score": 0-100の整数,
  "sections": [
    {
      "name": "セクション名",
      "score": 0-100の整数,
      "items": [
        {
          "label": "チェック項目名",
          "status": "good|warning|critical",
          "current_value": "現在の状態",
          "recommendation": "具体的な改善策（不要ならnull）"
        }
      ]
    }
  ],
  "action_list": [
    {
      "priority": "high|medium|low",
      "action": "具体的なアクション",
      "section": "関連セクション名"
    }
  ]
}"""


async def analyze_site(crawl_result: CrawlResult) -> dict:
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    crawl_data = asdict(crawl_result)
    # HTMLは長すぎるのでトリミング（最初の5000文字 + メタ情報）
    if len(crawl_data.get("html", "")) > 5000:
        crawl_data["html"] = crawl_data["html"][:5000] + "\n... (truncated)"

    user_message = f"""以下のWebサイトのクロールデータを分析してください。

## クロールデータ
```json
{json.dumps(crawl_data, ensure_ascii=False, indent=2)}
```

## 出力形式
以下のJSON形式で出力してください:
```json
{ANALYSIS_OUTPUT_SCHEMA}
```

JSONのみを出力し、それ以外のテキストは含めないでください。"""

    response = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=ANALYSIS_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    # Parse response
    response_text = response.content[0].text.strip()

    # Extract JSON from possible markdown code block
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

    report = json.loads(response_text)

    # Track API usage
    usage = {
        "model": "claude-sonnet-4-6",
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "cost_usd": _estimate_cost(
            response.usage.input_tokens,
            response.usage.output_tokens,
            "claude-sonnet-4-6",
        ),
    }

    return {"report": report, "usage": usage}


def _estimate_cost(input_tokens: int, output_tokens: int, model: str) -> float:
    # Sonnet 4.6 pricing (approximate)
    if "sonnet" in model:
        return (input_tokens * 3.0 / 1_000_000) + (output_tokens * 15.0 / 1_000_000)
    # Haiku 4.5 pricing
    elif "haiku" in model:
        return (input_tokens * 0.80 / 1_000_000) + (output_tokens * 4.0 / 1_000_000)
    return 0.0
