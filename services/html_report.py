"""
HTMLレポートを生成するユーティリティ（リッチデザイン版）
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List


def _render_body_html(body: str) -> str:
    """
    スライドの本文テキストをHTMLに整形
    """
    lines = [ln.rstrip() for ln in body.split("\n") if ln.strip()]
    html_chunks: List[str] = []
    bullet_buffer: List[str] = []

    def flush_bullets():
        nonlocal bullet_buffer
        if bullet_buffer:
            items = "".join(f"<li>{item}</li>" for item in bullet_buffer)
            html_chunks.append(f"<ul class='bullet-list'>{items}</ul>")
            bullet_buffer.clear()

    for line in lines:
        if line.startswith("###"):
            flush_bullets()
            html_chunks.append(f"<h4>{line.lstrip('#').strip()}</h4>")
            continue

        stripped = line.lstrip()
        if stripped.startswith("- "):
            bullet_buffer.append(stripped[2:].strip())
            continue

        flush_bullets()
        html_chunks.append(f"<p>{line}</p>")

    flush_bullets()
    return "".join(html_chunks)


def create_html_report(
    slides_data: List[Dict],
    title: str = "アイデア創出レポート",
    company_name: str = "",
    output_dir: str = "outputs",
) -> str:
    """
    スライド構成データをリッチなHTMLレポートとして書き出す
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    basename = f"{company_name or 'report'}-{timestamp}.html"
    output_path = Path(output_dir) / basename

    hero_title = company_name or title
    hero_subtitle = "戦略レポート"

    sections_html: List[str] = []
    section_index = 0
    for slide in slides_data:
        slide_type = slide.get("type")
        if slide_type == "title":
            hero_title = slide.get("title", hero_title)
            hero_subtitle = slide.get("subtitle", hero_subtitle)
        elif slide_type == "section":
            section_index += 1
            sections_html.append(
                f"<div class='section-label'><span class='pill'>SECTION {section_index:02d}</span>{slide.get('title','')}</div>"
            )
        elif slide_type == "content":
            body_html = _render_body_html(slide.get("body", ""))
            sections_html.append(
                f"""
                <article class="card">
                  <div class="card-header">
                    <div class="eyebrow">INSIGHT</div>
                    <h3>{slide.get('title','')}</h3>
                  </div>
                  <div class="card-body">
                    {body_html}
                  </div>
                </article>
                """
            )

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{hero_title}</title>
  <style>
    :root {{
      --bg: #050914;
      --panel: rgba(255,255,255,0.08);
      --text: #e7ecf5;
      --muted: #9aa3b5;
      --accent: #7dd3fc;
      --accent-2: #c084fc;
      --card: rgba(255,255,255,0.08);
      --border: rgba(255,255,255,0.18);
      --shadow: 0 25px 80px rgba(0,0,0,0.4);
      --glass: rgba(255,255,255,0.04);
      --glow: 0 10px 40px rgba(125,211,252,0.25), 0 10px 50px rgba(192,132,252,0.18);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      padding: 0;
      font-family: 'DM Sans','Segoe UI','Helvetica Neue',system-ui,sans-serif;
      background:
        radial-gradient(1200px circle at 10% 10%, rgba(125,211,252,0.12), transparent 30%),
        radial-gradient(900px circle at 80% 0%, rgba(192,132,252,0.14), transparent 28%),
        radial-gradient(1200px circle at 70% 70%, rgba(56,189,248,0.08), transparent 35%),
        linear-gradient(135deg, #050914 0%, #0a0f1f 30%, #0b1024 100%);
      color: var(--text);
      line-height: 1.7;
      min-height: 100vh;
    }}
    .ambient {{
      position: fixed;
      inset: 0;
      pointer-events: none;
      z-index: 0;
      mix-blend-mode: screen;
      opacity: 0.45;
      background:
        radial-gradient(500px circle at 20% 40%, rgba(125,211,252,0.14), transparent 50%),
        radial-gradient(420px circle at 75% 20%, rgba(192,132,252,0.16), transparent 50%),
        radial-gradient(360px circle at 40% 80%, rgba(94,234,212,0.12), transparent 55%);
      filter: blur(20px);
    }}
    header {{
      padding: 64px 24px 32px;
      text-align: center;
      position: relative;
      z-index: 1;
    }}
    .hero {{
      max-width: 900px;
      margin: 0 auto;
      padding: 32px;
      background: linear-gradient(120deg, rgba(125,211,252,0.18), rgba(192,132,252,0.22));
      border: 1px solid var(--border);
      border-radius: 24px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(10px);
      position: relative;
      overflow: hidden;
    }}
    .hero::before {{
      content: '';
      position: absolute;
      inset: 0;
      background: radial-gradient(500px circle at 20% 20%, rgba(255,255,255,0.08), transparent 40%);
      pointer-events: none;
    }}
    .hero h1 {{
      margin: 0 0 12px;
      font-size: clamp(28px, 4vw, 42px);
      letter-spacing: 0.4px;
    }}
    .hero p {{
      margin: 0;
      color: var(--muted);
      font-size: 16px;
    }}
    .meta {{
      display: inline-flex;
      gap: 10px;
      align-items: center;
      margin-top: 10px;
      color: var(--muted);
      font-size: 13px;
      letter-spacing: 0.2px;
    }}
    .meta .pill {{
      background: var(--glass);
      border: 1px solid var(--border);
      padding: 6px 12px;
      border-radius: 999px;
      color: var(--text);
      box-shadow: var(--glow);
    }}
    main {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 0 24px 60px;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 18px;
      position: relative;
      z-index: 1;
    }}
    .section-label {{
      grid-column: 1 / -1;
      color: var(--muted);
      letter-spacing: 0.08em;
      font-size: 13px;
      text-transform: uppercase;
      margin-top: 20px;
      margin-bottom: -6px;
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .section-label .pill {{
      background: rgba(255,255,255,0.08);
      border: 1px solid var(--border);
      padding: 6px 12px;
      border-radius: 999px;
      color: var(--text);
      font-weight: 700;
      letter-spacing: 0.08em;
      box-shadow: var(--glow);
    }}
    .card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 18px 18px 20px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(6px);
      transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
      position: relative;
      overflow: hidden;
    }}
    .card:hover {{
      transform: translateY(-4px);
      border-color: rgba(125,211,252,0.5);
      box-shadow: 0 20px 60px rgba(0,0,0,0.3), var(--glow);
    }}
    .card::after {{
      content: '';
      position: absolute;
      inset: 0;
      background: radial-gradient(400px circle at 120% -20%, rgba(125,211,252,0.1), transparent 50%);
      pointer-events: none;
    }}
    .card-header {{
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 8px;
    }}
    .eyebrow {{
      padding: 6px 10px;
      border-radius: 999px;
      background: rgba(255,255,255,0.07);
      border: 1px solid var(--border);
      font-size: 11px;
      letter-spacing: 0.08em;
      color: var(--muted);
    }}
    .card h3 {{
      margin: 0 0 10px;
      font-size: 18px;
      letter-spacing: 0.2px;
    }}
    .card-body p {{
      margin: 6px 0 10px;
      color: var(--muted);
    }}
    .card-body h4 {{
      margin: 10px 0 6px;
      font-size: 15px;
      color: var(--text);
    }}
    .bullet-list {{
      margin: 8px 0 12px 0;
      padding-left: 18px;
      color: var(--muted);
    }}
    .bullet-list li {{
      margin: 4px 0;
    }}
    footer {{
      text-align: center;
      color: var(--muted);
      font-size: 13px;
      padding: 18px;
      border-top: 1px solid var(--border);
      background: rgba(255,255,255,0.02);
      backdrop-filter: blur(8px);
      position: relative;
      z-index: 1;
    }}
  </style>
</head>
<body>
  <div class="ambient"></div>
  <header>
    <div class="hero">
      <p>{hero_subtitle}</p>
      <h1>{hero_title}</h1>
      <p>{title}</p>
      <div class="meta">
        <span class="pill">Generated</span>
        <span>{datetime.now().strftime("%Y-%m-%d %H:%M")}</span>
      </div>
    </div>
  </header>
  <main>
    {''.join(sections_html)}
  </main>
  <footer>Generated on {datetime.now().strftime("%Y-%m-%d %H:%M")}</footer>
</body>
</html>
"""

    output_path.write_text(html, encoding="utf-8")
    return str(output_path)
