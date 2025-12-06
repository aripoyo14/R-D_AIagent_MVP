"""
レポート生成サービス
戦略レポートを生成する
"""

# from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from typing import List, Dict
import os


# プロンプトテンプレート（関数の外に定義）
REPORT_SYSTEM_PROMPT = """あなたは化学メーカーの研究開発戦略コンサルタントです。
以下の情報を統合して、新規用途や改良アイデアを提案する戦略レポートをMarkdown形式で作成してください。

レポートは以下のセクションを含む必要があります：
1. **Trigger** - 今回の顧客の声（企業名・ニーズ）
2. **Chemical Insight** - 抽出された化学的課題
3. **Cross-Link** - 社内の他事業部にある類似知見（関連度とその理由）
4. **Market Trend** - 関連する市場の動き
5. **Proposal** - クラレとして提案すべき「新用途」または「改良アイデア」

各セクションは見出し（##）で区切り、具体的で実用的な内容を記載してください。
Markdown形式で出力してください。"""

REPORT_HUMAN_PROMPT = """以下の情報を基に戦略レポートを作成してください：

【顧客情報】
企業名: {company_name}

【面談内容】
{interview_content}

【抽出された技術タグ】
{tech_tags}

【他事業部の類似知見】
{cross_link_text}

【市場トレンド情報】
{market_trends}

上記の情報を統合して、戦略レポートをMarkdown形式で作成してください。"""


def format_cross_pollination_results(cross_pollination_results: List[Dict]) -> str:
    """
    他事業部の知見をフォーマットする
    
    Args:
        cross_pollination_results: 他事業部の検索結果
    
    Returns:
        str: フォーマットされたテキスト
    """
    if not cross_pollination_results:
        return "他事業部に類似する知見は見つかりませんでした。"
    
    cross_link_text = ""
    for i, result in enumerate(cross_pollination_results, 1):
        metadata = result.get("metadata", {})
        content = result.get("content", "")
        similarity = result.get("similarity", 0.0)
        
        cross_link_text += f"""
{i}. **{metadata.get('company_name', '不明')}** ({metadata.get('department', '不明')})
   - 部署・役職: {metadata.get('contact_info', '不明')}
   - 関連度: {similarity:.2%}
   - 内容要約: {content[:200]}...
"""
    
    return cross_link_text


def generate_idea_report(
    company_name: str,
    interview_content: str,
    tech_tags: List[str],
    cross_pollination_results: List[Dict],
    market_trends: str
) -> str:
    """
    Gemini 2.5 Proを使用して戦略レポートを生成する
    
    Args:
        company_name: 企業名
        interview_content: 面談内容
        tech_tags: 技術タグのリスト
        cross_pollination_results: 他事業部の検索結果
        market_trends: 市場トレンド情報
    
    Returns:
        str: Markdown形式のレポート
    """

    # Gemini 用チェック
    if ChatGoogleGenerativeAI is None:
        raise ImportError("Gemini を使うには langchain-google-genai のインストールが必要です")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY が設定されていません")

    # LLMを初期化
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.7,
        google_api_key=api_key,
    )
    
    # 他事業部の知見をフォーマット
    cross_link_text = format_cross_pollination_results(cross_pollination_results)
    
    # プロンプトテンプレート
    prompt = ChatPromptTemplate.from_messages([
        ("system", REPORT_SYSTEM_PROMPT),
        ("human", REPORT_HUMAN_PROMPT)
    ])
    
    # プロンプトをフォーマット
    formatted_prompt = prompt.format_messages(
        company_name=company_name,
        interview_content=interview_content,
        tech_tags=", ".join(tech_tags),
        cross_link_text=cross_link_text,
        market_trends=market_trends
    )
    
    # LLMを呼び出し
    response = llm.invoke(formatted_prompt)
    return response.content
