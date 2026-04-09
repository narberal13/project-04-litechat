"""ToSWatch crawler — fetches ToS pages and detects changes."""

import difflib
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup


@dataclass
class ToSSnapshot:
    target_id: str
    url: str
    text_content: str
    content_hash: str
    fetched_at: str
    error: str | None = None


async def fetch_tos_page(target_id: str, url: str) -> ToSSnapshot:
    """Fetch a ToS page and extract text content."""
    now = datetime.now(timezone.utc).isoformat()

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                page = await browser.new_page()
                await page.goto(url, wait_until="networkidle", timeout=30000)
                html = await page.content()

                # Extract main text content
                soup = BeautifulSoup(html, "lxml")

                # Remove script, style, nav, header, footer elements
                for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
                    tag.decompose()

                text = soup.get_text(separator="\n", strip=True)
                # Normalize whitespace
                lines = [line.strip() for line in text.splitlines() if line.strip()]
                text_content = "\n".join(lines)

                content_hash = hashlib.sha256(text_content.encode("utf-8")).hexdigest()

                return ToSSnapshot(
                    target_id=target_id,
                    url=url,
                    text_content=text_content,
                    content_hash=content_hash,
                    fetched_at=now,
                )
            finally:
                await browser.close()

    except Exception as e:
        return ToSSnapshot(
            target_id=target_id,
            url=url,
            text_content="",
            content_hash="",
            fetched_at=now,
            error=str(e),
        )


def compute_diff(old_text: str, new_text: str) -> str | None:
    """Compute unified diff between two text versions. Returns None if no changes."""
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()

    diff = list(difflib.unified_diff(old_lines, new_lines, lineterm=""))
    if not diff:
        return None

    return "\n".join(diff)


def extract_changed_sections(diff_text: str) -> list[str]:
    """Extract only the changed lines (additions and removals) from a unified diff."""
    changes = []
    for line in diff_text.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            changes.append(f"追加: {line[1:].strip()}")
        elif line.startswith("-") and not line.startswith("---"):
            changes.append(f"削除: {line[1:].strip()}")
    return changes
