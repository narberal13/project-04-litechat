"""Generate PDF reports from SiteScan API results."""

import json
import sys
import os
from datetime import datetime

# Simple HTML-based PDF generation using basic file output
# Since we don't have weasyprint locally, generate rich HTML files that can be printed to PDF

def generate_report_html(scan_data: dict) -> str:
    report = scan_data.get("report", {})
    url = scan_data.get("url", "N/A")
    completed_at = scan_data.get("completed_at", "")
    overall_score = report.get("overall_score", 0)
    summary = report.get("summary", "")
    sections = report.get("sections", [])
    action_list = report.get("action_list", [])

    date_str = ""
    if completed_at:
        try:
            dt = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
            date_str = dt.strftime("%Y年%m月%d日 %H:%M")
        except Exception:
            date_str = completed_at[:10]

    def score_color(score):
        if score >= 80: return "#10b981"
        if score >= 50: return "#f59e0b"
        return "#ef4444"

    def status_badge(status):
        colors = {
            "good": ("#d1fae5", "#065f46", "OK"),
            "warning": ("#fef3c7", "#92400e", "注意"),
            "critical": ("#fee2e2", "#991b1b", "要改善"),
        }
        bg, fg, label = colors.get(status, ("#f3f4f6", "#666", status))
        return f'<span style="background:{bg};color:{fg};padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700">{label}</span>'

    def priority_badge(priority):
        colors = {
            "high": ("#fee2e2", "#991b1b", "高"),
            "medium": ("#fef3c7", "#92400e", "中"),
            "low": ("#e0e7ff", "#3730a3", "低"),
        }
        bg, fg, label = colors.get(priority, ("#f3f4f6", "#666", priority))
        return f'<span style="background:{bg};color:{fg};padding:2px 10px;border-radius:4px;font-size:11px;font-weight:700">{label}</span>'

    sections_html = ""
    for section in sections:
        items_html = ""
        for item in section.get("items", []):
            rec_html = ""
            if item.get("recommendation"):
                rec_html = f'<div style="background:#eff6ff;padding:8px 12px;border-radius:6px;margin-top:6px;font-size:12px"><strong>改善策:</strong> {item["recommendation"]}</div>'
            items_html += f'''
            <div style="padding:10px 14px;background:#fafbfc;border-radius:6px;margin-bottom:8px">
                <div style="margin-bottom:4px">{status_badge(item.get("status",""))} <strong style="font-size:13px">{item.get("label","")}</strong></div>
                <div style="color:#6b7280;font-size:12px">{item.get("current_value","")}</div>
                {rec_html}
            </div>'''

        s_score = section.get("score", 0)
        sections_html += f'''
        <div style="background:white;border:1px solid #e5e7eb;border-radius:12px;padding:24px;margin-bottom:16px;page-break-inside:avoid">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
                <h2 style="margin:0;font-size:18px">{section.get("name","")}</h2>
                <div style="width:48px;height:48px;border-radius:50%;background:{score_color(s_score)};color:white;display:flex;align-items:center;justify-content:center;font-size:18px;font-weight:800">{s_score}</div>
            </div>
            {items_html}
        </div>'''

    actions_html = ""
    for i, action in enumerate(action_list):
        actions_html += f'''
        <div style="display:flex;align-items:center;gap:10px;padding:10px 14px;background:#fafbfc;border-radius:6px;margin-bottom:6px">
            <div style="width:24px;height:24px;border-radius:50%;background:#e5e7eb;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;flex-shrink:0">{i+1}</div>
            {priority_badge(action.get("priority",""))}
            <span style="font-size:13px">{action.get("action","")}</span>
        </div>'''

    html = f'''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>SiteScan Report - {url}</title>
<style>
    @page {{ margin: 20mm; size: A4; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Hiragino Sans", "Noto Sans JP", sans-serif; color: #1a1a2e; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 40px 20px; }}
    h1, h2, h3 {{ margin: 0; }}
</style>
</head>
<body>

<!-- Header -->
<div style="display:flex;justify-content:space-between;align-items:center;padding-bottom:24px;border-bottom:2px solid #2563eb;margin-bottom:32px">
    <div>
        <div style="font-size:12px;color:#2563eb;font-weight:700;letter-spacing:2px;margin-bottom:4px">SITESCAN REPORT</div>
        <h1 style="font-size:24px;margin-bottom:4px">Webサイト診断レポート</h1>
        <div style="color:#6b7280;font-size:13px">{url}</div>
        <div style="color:#6b7280;font-size:12px">診断日: {date_str}</div>
    </div>
    <div style="text-align:center">
        <div style="width:80px;height:80px;border-radius:50%;background:{score_color(overall_score)};color:white;display:flex;align-items:center;justify-content:center;font-size:28px;font-weight:800">{overall_score}</div>
        <div style="font-size:11px;color:#6b7280;margin-top:4px">総合スコア</div>
    </div>
</div>

<!-- Summary -->
<div style="background:white;border:1px solid #e5e7eb;border-left:4px solid #2563eb;border-radius:12px;padding:20px;margin-bottom:24px">
    <h2 style="font-size:16px;margin-bottom:8px">エグゼクティブサマリー</h2>
    <p style="color:#6b7280;font-size:14px;margin:0">{summary}</p>
</div>

<!-- Sections -->
{sections_html}

<!-- Action List -->
<div style="background:white;border:1px solid #e5e7eb;border-radius:12px;padding:24px;margin-bottom:24px;page-break-inside:avoid">
    <h2 style="font-size:18px;margin-bottom:16px">改善アクションリスト（優先度順）</h2>
    {actions_html}
</div>

<!-- Footer -->
<div style="text-align:center;color:#6b7280;font-size:11px;padding-top:24px;border-top:1px solid #e5e7eb">
    <p>このレポートは SiteScan (https://pik-tal.com) により自動生成されました</p>
    <p>診断結果は参考情報であり、成果を保証するものではありません</p>
</div>

</body>
</html>'''
    return html


def main():
    if len(sys.argv) < 3:
        print("Usage: python generate-pdf.py <scan_json_file> <output_html_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    with open(input_file, "r", encoding="utf-8") as f:
        scan_data = json.load(f)

    html = generate_report_html(scan_data)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Report generated: {output_file}")


if __name__ == "__main__":
    main()
