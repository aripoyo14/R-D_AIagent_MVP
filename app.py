"""
R&D Brain - Main Streamlit Application
営業担当者が面談録を入力し、AIが内容を精査するインターフェース
"""

import streamlit as st
from backend import save_interview_note, search_cross_pollination, search_market_trends
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import json
from datetime import datetime


# 事業部のリスト
DEPARTMENTS = [
    "エバール事業部",
    "イソプレン事業部",
    "ジェネスタ事業部"
]


# AIレビュー結果の構造化モデル
class ReviewResult(BaseModel):
    """AIレビューの結果を格納するモデル"""
    is_sufficient: bool = Field(description="情報が十分かどうか")
    questions: List[str] = Field(default=[], description="情報不足の場合の質問リスト")
    summary: Optional[str] = Field(default=None, description="内容の要約")
    tech_tags: List[str] = Field(default=[], description="抽出された技術タグ")


def check_api_keys() -> bool:
    """APIキーの設定状況を確認"""
    try:
        has_supabase = "supabase" in st.secrets and "url" in st.secrets["supabase"] and "key" in st.secrets["supabase"]
        has_openai = "openai" in st.secrets and "api_key" in st.secrets["openai"]
        return has_supabase and has_openai
    except:
        return False


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
        openai_api_key=st.secrets["openai"]["api_key"]
    )
    
    # 出力パーサーを設定
    parser = PydanticOutputParser(pydantic_object=ReviewResult)
    
    # プロンプトテンプレート
    prompt = ChatPromptTemplate.from_messages([
        ("system", """あなたは化学メーカーの研究開発部門の専門家です。
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

{format_instructions}"""),
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
        st.warning(f"AIレビューの解析に失敗しました: {str(e)}")
        return ReviewResult(
            is_sufficient=False,
            questions=["内容を確認できませんでした。もう一度お試しください。"]
        )


def generate_idea_report(
    company_name: str,
    interview_content: str,
    tech_tags: List[str],
    cross_pollination_results: List[Dict],
    market_trends: str
) -> str:
    """
    GPT-4oを使用して戦略レポートを生成する
    
    Args:
        company_name: 企業名
        interview_content: 面談内容
        tech_tags: 技術タグのリスト
        cross_pollination_results: 他事業部の検索結果
        market_trends: 市場トレンド情報
    
    Returns:
        str: Markdown形式のレポート
    """
    # LLMを初期化
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.7,
        openai_api_key=st.secrets["openai"]["api_key"]
    )
    
    # 他事業部の知見をフォーマット
    cross_link_text = ""
    if cross_pollination_results:
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
    else:
        cross_link_text = "他事業部に類似する知見は見つかりませんでした。"
    
    # プロンプトテンプレート
    prompt = ChatPromptTemplate.from_messages([
        ("system", """あなたは化学メーカーの研究開発戦略コンサルタントです。
以下の情報を統合して、新規用途や改良アイデアを提案する戦略レポートをMarkdown形式で作成してください。

レポートは以下のセクションを含む必要があります：
1. **Trigger** - 今回の顧客の声（企業名・ニーズ）
2. **Chemical Insight** - 抽出された化学的課題
3. **Cross-Link** - 社内の他事業部にある類似知見（関連度とその理由）
4. **Market Trend** - 関連する市場の動き
5. **Proposal** - クラレとして提案すべき「新用途」または「改良アイデア」

各セクションは見出し（##）で区切り、具体的で実用的な内容を記載してください。
Markdown形式で出力してください。"""),
        ("human", """以下の情報を基に戦略レポートを作成してください：

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

上記の情報を統合して、戦略レポートをMarkdown形式で作成してください。""")
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


def display_cross_pollination_cards(results: List[Dict]):
    """
    他事業部の面談録をカード形式で表示する
    
    Args:
        results: 検索結果のリスト
    """
    if not results:
        st.info("他事業部に類似する知見は見つかりませんでした。")
        return
    
    for i, result in enumerate(results, 1):
        metadata = result.get("metadata", {})
        content = result.get("content", "")
        similarity = result.get("similarity", 0.0)
        
        with st.container():
            st.markdown(f"""
            <div style="
                border: 1px solid #ddd;
                border-radius: 10px;
                padding: 15px;
                margin: 10px 0;
                background-color: #f9f9f9;
            ">
                <h4 style="margin-top: 0;">📋 知見 #{i}</h4>
                <p><strong>企業名:</strong> {metadata.get('company_name', '不明')}</p>
                <p><strong>事業部:</strong> {metadata.get('department', '不明')}</p>
                <p><strong>部署・役職:</strong> {metadata.get('contact_info', '不明')}</p>
                <p><strong>関連度:</strong> <span style="color: #1f77b4; font-weight: bold;">{similarity:.1%}</span></p>
                <p><strong>内容要約:</strong></p>
                <p style="background-color: white; padding: 10px; border-radius: 5px;">{content[:300]}{'...' if len(content) > 300 else ''}</p>
            </div>
            """, unsafe_allow_html=True)


def main():
    """メインアプリケーション"""
    st.set_page_config(
        page_title="R&D Brain - 面談録登録",
        page_icon="🧪",
        layout="wide"
    )
    
    st.title("🧪 R&D Brain - 面談録登録システム")
    st.markdown("営業担当者が面談録を入力し、AIが内容を精査します")
    
    # サイドバー
    with st.sidebar:
        st.header("⚙️ 設定")
        
        # 事業部選択
        selected_department = st.selectbox(
            "事業部を選択",
            DEPARTMENTS,
            index=0
        )
        
        st.divider()
        
        # APIキー設定状況
        st.subheader("🔑 APIキー設定状況")
        api_keys_ok = check_api_keys()
        if api_keys_ok:
            st.success("✅ すべてのAPIキーが設定されています")
        else:
            st.error("❌ APIキーが設定されていません")
            st.info("`.streamlit/secrets.toml` に設定してください")
    
    # メインコンテンツ
    if not api_keys_ok:
        st.warning("⚠️ APIキーが設定されていないため、機能を利用できません。")
        return
    
    # セッションステートの初期化
    if "review_result" not in st.session_state:
        st.session_state.review_result = None
    if "form_data" not in st.session_state:
        st.session_state.form_data = {}
    if "idea_report" not in st.session_state:
        st.session_state.idea_report = None
    if "show_idea_report" not in st.session_state:
        st.session_state.show_idea_report = False
    
    # 入力フォーム
    with st.form("interview_form", clear_on_submit=False):
        st.header("📝 面談情報入力")
        
        company_name = st.text_input(
            "企業名 (Company Name)",
            value=st.session_state.form_data.get("company_name", ""),
            placeholder="例: トヨタ自動車"
        )
        
        contact_info = st.text_input(
            "相手方 部署・役職",
            value=st.session_state.form_data.get("contact_info", ""),
            placeholder="例: ボディ設計部 課長"
        )
        
        interview_memo = st.text_area(
            "面談メモ (Raw Content)",
            value=st.session_state.form_data.get("interview_memo", ""),
            height=300,
            placeholder="面談の内容を自由に記述してください..."
        )
        
        submitted = st.form_submit_button("AIレビュー実行", type="primary", use_container_width=True)
        
        if submitted:
            if not interview_memo.strip():
                st.error("⚠️ 面談メモを入力してください")
            else:
                # フォームデータを保存
                st.session_state.form_data = {
                    "company_name": company_name,
                    "contact_info": contact_info,
                    "interview_memo": interview_memo
                }
                
                # AIレビューを実行
                with st.spinner("🤖 AIが内容をレビュー中..."):
                    review_result = review_interview_content(interview_memo)
                    st.session_state.review_result = review_result
    
    # AIレビュー結果の表示
    if st.session_state.review_result:
        st.divider()
        st.header("🤖 AIレビュー結果")
        
        review = st.session_state.review_result
        
        if review.is_sufficient:
            # 情報が十分な場合
            st.success("✅ 情報が十分です。登録可能な状態です。")
            
            # 要約を表示
            if review.summary:
                st.subheader("📋 内容要約")
                st.info(review.summary)
            
            # 技術タグを表示
            if review.tech_tags:
                st.subheader("🏷️ 抽出された技術タグ")
                tags_display = " ".join([f"`{tag}`" for tag in review.tech_tags])
                st.markdown(tags_display)
            
            # 登録ボタン
            st.divider()
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("この内容で登録しますか？", type="primary", use_container_width=True):
                    # メタデータを準備
                    metadata = {
                        "company_name": st.session_state.form_data.get("company_name", ""),
                        "contact_info": st.session_state.form_data.get("contact_info", ""),
                        "department": selected_department,
                        "tech_tags": review.tech_tags,
                        "created_at": datetime.now().isoformat()
                    }
                    
                    # 保存
                    with st.spinner("💾 データを保存中..."):
                        success = save_interview_note(
                            text=st.session_state.form_data.get("interview_memo", ""),
                            metadata=metadata
                        )
                    
                    if success:
                        st.success("✅ データが正常に保存されました！")
                        st.balloons()
                        
                        # アイデア創出プロセスを実行
                        with st.spinner("💡 アイデア創出プロセスを実行中..."):
                            # 1. 社内シーズの探索
                            st.info("🔍 社内の他事業部の知見を探索中...")
                            interview_content = st.session_state.form_data.get("interview_memo", "")
                            cross_pollination_results = search_cross_pollination(
                                query_text=interview_content,
                                current_department=selected_department,
                                top_k=3
                            )
                            
                            # 2. 市場調査
                            st.info("🌐 市場トレンドを調査中...")
                            market_trends = search_market_trends(
                                tech_tags=review.tech_tags,
                                use_case=review.summary or ""
                            )
                            
                            # 3. 戦略レポート生成
                            st.info("📊 戦略レポートを生成中...")
                            idea_report = generate_idea_report(
                                company_name=st.session_state.form_data.get("company_name", ""),
                                interview_content=interview_content,
                                tech_tags=review.tech_tags,
                                cross_pollination_results=cross_pollination_results,
                                market_trends=market_trends
                            )
                            
                            # セッションステートに保存
                            st.session_state.idea_report = idea_report
                            st.session_state.cross_pollination_results = cross_pollination_results
                            st.session_state.show_idea_report = True
                        
                        # フォームデータとレビュー結果は保持（レポート表示のため）
                        st.rerun()
                    else:
                        st.error("❌ データの保存に失敗しました")
        else:
            # 情報が不足している場合
            st.warning("⚠️ 情報が不足しています。以下の点について確認してください。")
            
            if review.questions:
                st.subheader("❓ 追加で確認すべき質問")
                for i, question in enumerate(review.questions, 1):
                    st.markdown(f"{i}. {question}")
            
            st.info("💡 具体的な数値や、現行品の問題点などを追加で記入してください。")
    
    # アイデア創出レポートの表示
    if st.session_state.show_idea_report and st.session_state.idea_report:
        st.divider()
        st.header("💡 アイデア創出レポート")
        st.markdown("---")
        
        # レポート本文を表示
        st.markdown(st.session_state.idea_report)
        
        st.divider()
        
        # 他事業部の知見をカード形式で表示
        if "cross_pollination_results" in st.session_state:
            st.subheader("🔗 参考: 他事業部の類似知見")
            display_cross_pollination_cards(st.session_state.cross_pollination_results)
        
        st.divider()
        
        # リセットボタン
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("新しい面談録を登録する", type="primary", use_container_width=True):
                # セッションステートをクリア
                st.session_state.review_result = None
                st.session_state.form_data = {}
                st.session_state.idea_report = None
                st.session_state.cross_pollination_results = []
                st.session_state.show_idea_report = False
                st.rerun()


if __name__ == "__main__":
    main()

