"""
AIを活用してHTMLスライド（Reveal.js）を生成するエージェント
"""

from __future__ import annotations

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

SYSTEM_PROMPT = """あなたはプロフェッショナルなプレゼンテーションデザイナー兼AIエージェントです。
提供されたスライド構成データ（JSON）をもとに、Reveal.jsを使用した美しく、インパクトのあるHTMLスライドを作成してください。

# 要件
1. **Reveal.jsの使用**: 最新のReveal.js（CDN経由）を使用してください。
2. **デザインの多様性**: 
   - 毎回、コンテンツの雰囲気に合わせてテーマや配色（CSS変数など）を調整してください。
   - "Futuristic", "Corporate", "Elegant", "Bold" など、ランダム性を持たせて毎回少し違う雰囲気に仕上げてください。
   - 背景にはCSSグラデーションや、シンプルなパターンを使用し、リッチに見せてください。
3. **レイアウトの工夫**:
   - 単なる箇条書きだけでなく、2カラムレイアウト、大きな文字での強調、引用スタイルなどを適切に使い分けてください。
   - `r-fit-text` クラスや `fragment` クラスを使って、動的な演出を加えてください。
4. **完全なHTML出力**:
   - `<!doctype html>` から始まる完全なHTMLファイルを出力してください。
   - CSSは `<style>` タグ内に記述してください。
   - Markdownやコードブロックは含めず、HTMLコードのみを出力してください。

# 入力データ構造
JSON形式のリストで、各要素は `type` ("title", "section", "content") と `title`, `body` などを持ちます。
"""

HUMAN_PROMPT = """以下のスライド構成データを使って、最高のスライドを作成してください。

【企業名】
{company_name}

【スライドデータ】
{slides_data_json}

出力はHTMLコードのみにしてください。"""

# スライド操作のUIを左右中央に配置するためのCSS
NAVIGATION_CSS = """
<style>
  .reveal .controls {
    top: 50%;
    left: 32px;
    right: 32px;
    bottom: auto;
    transform: translateY(-50%);
    display: flex;
    justify-content: space-between;
    align-items: center;
    pointer-events: none;
  }
  .reveal .controls button {
    pointer-events: auto;
    width: 52px;
    height: 52px;
    border-radius: 999px;
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.25);
    backdrop-filter: blur(6px);
    background: rgba(20, 20, 30, 0.55);
  }
  .reveal .controls .navigate-up,
  .reveal .controls .navigate-down {
    display: none;
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
</style>
"""

def create_slide_report(
    slides_data: List[Dict],
    title: str = "アイデア創出レポート",
    company_name: str = "",
    output_dir: str = "outputs",
) -> str:
    """
    AIを使用してスライド構成データをリッチなReveal.jsスライドに変換する
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    basename = f"slide-{company_name or 'report'}-{timestamp}.html"
    output_path = Path(output_dir) / basename

    # LLMの初期化 (Gemini 2.5 Pro)
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-pro",
        # model="gemini-2.5-flash-lite",
        temperature=0.9,
        google_api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
        convert_system_message_to_human=True # System prompt support varies
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", HUMAN_PROMPT)
    ])

    chain = prompt | llm | StrOutputParser()

    # データをJSON文字列に変換
    slides_json = json.dumps(slides_data, ensure_ascii=False, indent=2)

    try:
        # AIによる生成実行
        html_content = chain.invoke({
            "company_name": company_name or title,
            "slides_data_json": slides_json
        })

        # コードブロック記法が含まれている場合の除去処理
        html_content = html_content.replace("```html", "").replace("```", "").strip()

        # 次へボタンを中央寄りに配置するCSSを差し込む
        if "</head>" in html_content:
            html_content = html_content.replace("</head>", f"{NAVIGATION_CSS}\n</head>", 1)
        else:
            html_content = NAVIGATION_CSS + html_content

        output_path.write_text(html_content, encoding="utf-8")
        return str(output_path)

    except Exception as e:
        print(f"Error generating slides with AI: {e}")
        raise e
