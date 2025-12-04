"""
AIレビューサービス
面談内容をAIがレビューし、情報の十分性を評価する
"""

# from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from typing import List, Optional
import os
import logging

logger = logging.getLogger(__name__)


# AIレビュー結果の構造化モデル
class ReviewResult(BaseModel):
    """AIレビューの結果を格納するモデル"""
    is_sufficient: bool = Field(description="情報が十分かどうか")
    questions: List[str] = Field(default=[], description="情報不足の場合の質問リスト")
    summary: Optional[str] = Field(default=None, description="内容の要約")
    tech_tags: List[str] = Field(default=[], description="抽出された技術タグ")


# プロンプトテンプレート（関数の外に定義）
REVIEW_PROMPT_TEMPLATE = """あなたは化学メーカーの研究開発部門の専門家です。出力は必ず日本語で記載してください。
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
    Gemini 2.5 Proを使用して面談内容をレビューする
    
    Args:
        content: 面談メモの内容
    
    Returns:
        ReviewResult: レビュー結果
    """
    # # LLMを初期化
    # llm = ChatOpenAI(
    #     model="gpt-4o",
    #     temperature=0.3,
    #     openai_api_key=os.getenv("OPENAI_API_KEY")
    # )

    # Gemini 用のチェック
    if ChatGoogleGenerativeAI is None:
        raise ImportError("Gemini を使うには langchain-google-genai のインストールが必要です")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY が設定されていません")

    # LLMを初期化（Gemini 2.5 Pro）
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-pro",
        temperature=0.3,
        google_api_key=api_key,
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


def select_important_tags(tech_tags: List[str], interview_memo: str = "", max_tags: int = 5) -> List[str]:
    """
    抽出された技術タグから、化学系製造業にとって重要度の高いタグを選定する
    
    Args:
        tech_tags: 抽出された技術タグのリスト
        interview_memo: 面談メモ（オプション、文脈理解のため）
        max_tags: 選定する最大タグ数（デフォルト: 5）
    
    Returns:
        List[str]: 重要度の高いタグのリスト（最大max_tags件）
    """
    if not tech_tags:
        return []
    
    # タグが5つ以下の場合はそのまま返す
    if len(tech_tags) <= max_tags:
        logger.info(f"技術タグ数が{max_tags}以下なので、そのまま使用: {tech_tags}")
        return tech_tags
    
    # Gemini 用のチェック
    if ChatGoogleGenerativeAI is None:
        logger.warning("Gemini が利用できないため、最初の5つのタグを返します")
        return tech_tags[:max_tags]
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY が設定されていないため、最初の5つのタグを返します")
        return tech_tags[:max_tags]
    
    try:
        # LLMを初期化（Gemini 2.5 Flash - 高速で低コスト）
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.3,
            google_api_key=api_key,
        )
        
        # プロンプトの構築
        tags_str = "、".join(tech_tags)
        context = f"\n面談メモの要約: {interview_memo[:500]}" if interview_memo else ""
        
        prompt = f"""あなたは化学メーカーの研究開発部門の専門家です。
以下の技術タグから、化学系製造業にとって重要度の高いタグを{max_tags}つ選定してください。

【選定基準】
1. 材料名や化学物質名を優先
2. 用途や応用分野を優先
3. 具体的な物性や特性を優先
4. 技術領域やプロセス名を優先
5. 一般的すぎるキーワードは除外

【技術タグリスト】
{tags_str}
{context}

【出力形式】
選定したタグを番号付きリストで出力してください。各タグは元の表記をそのまま使用してください。
例:
1. タグ1
2. タグ2
3. タグ3
4. タグ4
5. タグ5

重要度の高い{max_tags}つのタグを選定してください:"""
        
        # LLMを呼び出し
        response = llm.invoke([HumanMessage(content=prompt)])
        result_text = response.content.strip()
        
        # 結果をパース（番号付きリストからタグを抽出）
        selected_tags = []
        lines = result_text.split('\n')
        for line in lines:
            line = line.strip()
            # 番号付きリストの形式を解析（例: "1. タグ名" または "1) タグ名"）
            if line and (line[0].isdigit() or line.startswith('・') or line.startswith('-') or line.startswith('*')):
                # 番号や記号を除去
                tag = line.split('.', 1)[-1].split(')', 1)[-1].strip()
                tag = tag.lstrip('・-* ').strip()
                if tag and tag in tech_tags:
                    selected_tags.append(tag)
        
        # パースに失敗した場合やタグ数が不足している場合のフォールバック
        if len(selected_tags) < max_tags:
            logger.warning(f"LLMが{len(selected_tags)}個のタグしか選定しませんでした。フォールバック処理を実行します。")
            # 元のタグリストから最初のmax_tags個を返す
            return tech_tags[:max_tags]
        
        logger.info(f"重要度の高い{len(selected_tags)}個のタグを選定: {selected_tags}")
        return selected_tags[:max_tags]
        
    except Exception as e:
        logger.error(f"技術タグの選定中にエラーが発生しました: {e}", exc_info=True)
        # エラー時は最初のmax_tags個を返す
        return tech_tags[:max_tags]
