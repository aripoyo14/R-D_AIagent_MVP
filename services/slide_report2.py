"""
Enhanced slide generator with business-friendly defaults, optional Chart.js,
and safer fallbacks for images and layouts.
"""

from __future__ import annotations

import os
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# System prompt: business tone + safe fallbacks for offline/missing data
SYSTEM_PROMPT = """
あなたは世界トップクラスのビジネスプレゼンテーションデザイナーです。
提供された構成データをもとに、Reveal.jsを使用した説得力のあるHTMLスライドを作成してください。

# トーン
- Smart / Trustworthy / Modern を基調にしつつ、5テーマをローテーション: Corporate Blue, Dark Minimal, Warm Gradient, Futuristic Neon, Glassmorphism。
- 見出しは Google Fonts（例: Space Grotesk / Manrope）、本文は Inter 系にし、フォールバックも指定。
- 全スライド単色禁止。必ずグラデーションやパターン（斜線・グリッド・ぼかしシェイプのいずれか）を背景に入れる。
- 重要数値は大きめフォントで強調。余白は広め、情報密度は詰め込みすぎない。

# 技術仕様
1. フレームワーク: Reveal.js (CDN) を必須。Tailwind CSS / FontAwesome / Chart.js は CDN で読み込む。
2. グラフ: 明示的な数値配列やパーセンテージが入力に含まれる場合のみ Chart.js で視覚化する。
   - データが曖昧/文中のみの場合はグラフ化せずテキストでまとめる。勝手に数値を捏造しない。
   - Chart.js はダーク背景で見えるネオン系カラー、角丸バー、薄いグリッド、Legendは右上浮遊を推奨。
3. 画像: 適切な場合のみ Unsplash 画像 `https://source.unsplash.com/featured/?keyword1,keyword2` を使う。
   - 読み込みに失敗した場合でも読めるよう、同じスライドにグラデ背景または単色背景を指定する。
   - 画像上に半透明オーバーレイ（例: background-color: rgba(0,0,0,0.55)）を重ね、テキスト可読性を確保。
4. レイアウト多様性: 左右2分割（画像/グラフ+テキスト）、3カード、フル背景+大見出し、引用+統計、タイムライン（水平ステップ）、インフォグラフィ風ブロックを最低2–3種類混在させる。全スライド同一レイアウトは禁止。
5. モーション: 見出しは fade-in-up、リストは fragment でステップ表示。1スライド内の効果は多くても2種まで。
6. グラス/ネオン感: カードやボックスに backdrop-filter: blur(8px) と半透明ボーダー、軽いネオンシャドウを入れて未来感を出す。
7. HTML出力: <!doctype html> から始まる完全なHTML。コードブロックは出力しない。Reveal.initialize を含める。
8. オフライン耐性: CDNが落ちても最低限読めるよう、本文・背景色・余白などの基本スタイルを <style> で記述する。
9. ナビゲーション: 右/左ボタンが縦中央に来るようなCSSを入れて操作しやすくする。
"""

HUMAN_PROMPT = """以下のスライド構成データを使って、最高のビジネススライドを作成してください。

【企業名/タイトル】
{company_name}

【スライドデータ】
{slides_data_json}

必須:
- Reveal.js を使用すること。
- 数値配列/％が明示されている場合のみ Chart.js でグラフ化すること（捏造禁止）。
- 画像を使う場合は Unsplash キーワード検索URLを使用し、同時にグラデ/単色の背景指定も入れること。
- CDNが使えない場合でも文字が読めるよう、基本色・余白・フォントサイズのベースCSSを <style> に含めること。
- 出力はHTMLコードのみ。Markdown記法や説明文は入れないこと。
"""

# Navigation CSS: place previous/next at vertical center, left/right sides
NAVIGATION_CSS = """
<style>
  .reveal .controls {
    top: auto;
    bottom: 32px;
    right: 32px;
    left: auto;
    transform: none;
    display: flex;
    gap: 24px;
    justify-content: flex-end;
    align-items: center;
    pointer-events: none;
  }
  .reveal .controls button {
    pointer-events: auto;
    width: 52px;
    height: 52px;
    border-radius: 999px;
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.35), 0 0 12px rgba(0, 255, 200, 0.4);
    backdrop-filter: blur(8px);
    background: linear-gradient(135deg, rgba(20, 20, 30, 0.6), rgba(30, 80, 120, 0.6));
    border: 1px solid rgba(0, 255, 200, 0.35);
  }
  .reveal .controls .navigate-up,
  .reveal .controls .navigate-down {
    display: none;
  }
  .reveal .controls .navigate-left {
    order: 1;
  }
  .reveal .controls .navigate-right {
    order: 2;
  }
  @media (max-width: 640px) {
    .reveal .controls {
      top: auto;
      bottom: 22px;
      left: 18px;
      right: 18px;
      transform: none;
    }
  }
  /* コンテンツが溢れたらスクロール可能にする */
  .reveal .slides > section {
    height: 100%;
    overflow-y: auto !important;
    overflow-x: hidden;
  }
</style>
"""


def create_slide_report_v2(
    slides_data: List[Dict],
    title: str = "市場調査レポート",
    company_name: str = "",
    output_dir: str = "outputs",
    model_name: str = "gemini-2.5-pro",
    temperature: float = 0.8,
) -> str:
    """
    AIを使用してデータをビジネススライドに変換する（Chart.js/Tailwind/Unsplash対応版）。
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_name = re.sub(r'[\\/:*?"<>|]+', "", company_name or title).replace(" ", "_")
    basename = f"slide-{safe_name}-{timestamp}.html"
    output_path = Path(output_dir) / basename

    llm = ChatGoogleGenerativeAI(
        # model="gemini-2.5-pro",
        model="gemini-2.5-flash",
        temperature=temperature,
        google_api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", HUMAN_PROMPT),
        ]
    )

    chain = prompt | llm | StrOutputParser()

    slides_json = json.dumps(slides_data, ensure_ascii=False, indent=2)

    try:
        html_content = chain.invoke(
            {
                "company_name": company_name or title,
                "slides_data_json": slides_json,
            }
        )

        # Cleanup markdown fences if any
        html_content = html_content.replace("```html", "").replace("```", "").strip()

        # Inject navigation CSS near </head>
        if "</head>" in html_content:
            html_content = html_content.replace("</head>", f"{NAVIGATION_CSS}\n</head>", 1)
        else:
            html_content = NAVIGATION_CSS + html_content

        output_path.write_text(html_content, encoding="utf-8")
        return str(output_path)
    except Exception as e:
        print(f"Error generating slides with AI: {e}")
        raise e


__all__ = ["create_slide_report_v2"]
