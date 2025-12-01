from __future__ import annotations

from typing import List, Dict


def parse_markdown_to_slides(markdown_text: str, company_name: str = "") -> List[Dict]:
    """
    戦略レポート（Markdown）を、HTMLレポート/スライド用の構造化データに変換するパーサ。

    戻り値の想定構造（services/html_report.py, slide_report.py と揃えている）:
        [
            {"type": "title", "title": "...", "subtitle": "..."},
            {"type": "section", "title": "Trigger"},
            {"type": "content", "title": "顧客の声", "body": "本文..."},
            ...
        ]
    """
    lines = markdown_text.splitlines()
    slides: List[Dict] = []

    # ---- 1枚目: タイトルスライド ----
    title_text = f"{company_name} 戦略レポート" if company_name else "アイデア創出レポート"
    slides.append(
        {
            "type": "title",
            "title": title_text,
            "subtitle": "R&D Brain レポート",
        }
    )

    current_section_title: str | None = None
    current_content: Dict | None = None
    body_lines: List[str] = []

    def flush_content() -> None:
        nonlocal current_content, body_lines
        if current_content is not None:
            current_content["body"] = "\n".join(body_lines).strip()
            slides.append(current_content)
        current_content = None
        body_lines = []

    for raw in lines:
        ln = raw.rstrip("\n")

        # セクション見出し: "## "
        if ln.startswith("## "):
            flush_content()
            current_section_title = ln[3:].strip()
            slides.append({"type": "section", "title": current_section_title})
            continue

        # セクション内コンテンツ見出し: "### "
        if ln.startswith("### "):
            flush_content()
            current_content = {
                "type": "content",
                "title": ln[4:].strip(),
                "body": "",
            }
            continue

        # それ以外は本文として貯める
        if not ln.strip():
            # 完全な空行はスキップ（必要なら残すように変更可）
            continue

        if current_content is None:
            # まだ content が始まっていない場合:
            # 直前のセクションがあればその内容として、なければ「概要」として扱う
            current_content = {
                "type": "content",
                "title": current_section_title or "概要",
                "body": "",
            }
        body_lines.append(ln)

    flush_content()
    return slides