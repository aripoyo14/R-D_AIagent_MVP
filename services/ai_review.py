"""
AIレビューサービス
面談内容をAIがレビューし、情報の十分性を評価する
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Optional
import os


# AIレビュー結果の構造化モデル
class ReviewResult(BaseModel):
    """AIレビューの結果を格納するモデル"""
    is_sufficient: bool = Field(description="情報が十分かどうか")
    questions: List[str] = Field(default=[], description="情報不足の場合の質問リスト")
    summary: Optional[str] = Field(default=None, description="内容の要約")
    tech_tags: List[str] = Field(default=[], description="抽出された技術タグ")


# プロンプトテンプレート（関数の外に定義）
REVIEW_PROMPT_TEMPLATE = """あなたは化学メーカーの研究開発部門の専門家です。
面談メモの内容を評価し、以下の基準で判断してください：

【評価基準】
- 化学的な「具体的なニーズ」が含まれているか？
  - 温度条件（例: 100℃以上、-20℃以下）
  - 強度・物性（例: 引張強度100MPa以上、弾性率）
  - 耐性（例: 耐熱性、耐薬品性、耐候性）
  - その他の具体的な数値や仕様

【出力形式】
- 情報が十分な場合: is_sufficient=true, summary（要約）とtech_tags（技術タグのリスト）を提供
- 情報が不足している場合: is_sufficient=false, questions（追加で聞くべき質問のリスト）を提供

技術タグは、材料名、用途、特性、技術領域などを含めてください。

{format_instructions}"""


def review_interview_content(content: str) -> ReviewResult:
    """
    GPT-4oを使用して面談内容をレビューする
    
    Args:
        content: 面談メモの内容
    
    Returns:
        ReviewResult: レビュー結果
    """
    # LLMを初期化
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.3,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # 出力パーサーを設定
    parser = PydanticOutputParser(pydantic_object=ReviewResult)
    
    # プロンプトテンプレート
    prompt = ChatPromptTemplate.from_messages([
        ("system", REVIEW_PROMPT_TEMPLATE),
        ("human", "以下の面談メモを評価してください：\n\n{content}")
    ])
    
    # プロンプトをフォーマット
    formatted_prompt = prompt.format_messages(
        content=content,
        format_instructions=parser.get_format_instructions()
    )
    
    # LLMを呼び出し
    response = llm.invoke(formatted_prompt)
    
    # 結果をパース
    try:
        result = parser.parse(response.content)
        return result
    except Exception as e:
        # パースに失敗した場合、デフォルト値を返す
        # エラーハンドリングは呼び出し側で行う
        return ReviewResult(
            is_sufficient=False,
            questions=[f"AIレビューの解析に失敗しました: {str(e)}。もう一度お試しください。"]
        )

