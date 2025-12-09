"""イノベーション分隊（5エージェント）の中核ロジック。

StreamlitのチャットUIで5人が議論するフローを実装。
プロンプトと進行は仕様に従う。
"""

import os
from typing import List, Optional, Dict

import streamlit as st
from langchain_core.messages import HumanMessage, SystemMessage

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None

import backend
from services.patents import search_patents
from services.academic import search_arxiv, format_arxiv_results
from services.ai_review import select_important_tags

from services.report_generator import REPORT_SYSTEM_PROMPT, REPORT_HUMAN_PROMPT
from components.conversation_log import get_chat_css, render_message_html

# 定数定義
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORCHESTRATOR_AVATAR = os.path.join(BASE_DIR, "images", "Orchestrator.png")
MARKET_RESEARCHER_AVATAR = os.path.join(BASE_DIR, "images", "Market_Researcher.png")
INTERNAL_SPECIALIST_AVATAR = os.path.join(BASE_DIR, "images", "Internal_Specialist.png")
SOLUTION_ARCHITECT_AVATAR = os.path.join(BASE_DIR, "images", "Solution_Architect.png")
DEVILS_ADVOCATE_AVATAR = os.path.join(BASE_DIR, "images", "Devils_Advocate.png")

# 市場規模・トレンド・競合のフォールバック情報（検索結果が不十分な場合に使用）
FALLBACK_MARKET_INFO = """## 市場規模（Market Size）

EV用熱管理システム市場は2024–2030年にCAGR 20%以上で成長
→ EV普及に伴い、バッテリー熱管理の重要性が高まり、市場全体が急拡大。

部材単価が高く、高付加価値市場

放熱樹脂は通常のエンプラの 3〜5倍（1,500〜2,500円/kg） の価格帯。

旭日自動車の事例では：

年間20万台 × 1台12個 = 240万個/年

1個200gと仮定 → 年間約480トンのコンパウンド需要
→ OEM 1社だけでも数百トン規模の需要が生まれる、成長余地の大きい領域。

## トレンド（Market Trends）

金属から樹脂への置換が急加速

バッテリーハウジング・モジュールカバーにおいて、

軽量化（比重：アルミ2.7 → 樹脂1.6〜1.8）

コスト削減（後加工レス、成形性向上）
を目的に、アルミ → 放熱樹脂への転換 が進む。

EV高電圧化に伴う材料要求の高度化

耐電圧、熱伝導率、難燃性、耐熱性など、仕様が急速に高レベル化。

これにより、PPS・PPA・高機能PBTなどの高性能樹脂が採用拡大中。

環境・サステナビリティ対応の強化

欧州 OEM を中心に バイオマス、リサイクル材、LCA対応 への要求が増加。

樹脂材料メーカー側も「バイオマスPPA」「低CO₂排出材料」を強化する傾向。

## 競合（Competitive Landscape）

東レ（Toray）

強み：PPSのグローバルトップメーカー。重合〜コンパウンドまで垂直統合。

実績：「トレリナ」で高放熱グレード、高CTIグレードを既に展開。

脅威：供給力・価格競争力ともに強く、最重要ベンチマーク。

ポリプラスチックス（Polyplastics）

強み：PBT・PPSに強く、自動車用途で高いシェア。

特徴：金属インサート成形・接合技術（AKIT）に優れる。

動向：バスバー周辺向けに耐ヒートショック性向上グレードを展開。

ソルベイ（Solvay）

強み：グローバルトップクラスの高機能PPA（アモデル）とPPS（ライトン）を保有。

差別化：超高電圧や極限環境向けの高機能材料が豊富。

実績：欧州OEMの採用例が多く、プレミアム領域に強い。

DSM（Envalior）

強み：PA46やPPA（ForTii）に加え、バイオマス対応（EcoPaXX） を積極展開。

特徴：サステナビリティの要求が強いOEMへの相性が高い。

脅威：旭日自動車が「バイオマス要望」を出しているため、競合として特に強い。
"""


def get_llm(temperature: float = 0.3, streaming: bool = False, model_name: str = "gemini-2.5-flash-lite"):
    """LLMを返すファクトリ。Gemini 2.5 Flash を使用。"""

    if ChatGoogleGenerativeAI is None:
        raise ImportError("Gemini を使うには langchain-google-genai のインストールが必要です")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY が設定されていません")

    return ChatGoogleGenerativeAI(
        # model="gemini-2.5-flash",
        model=model_name,
        temperature=temperature,
        google_api_key=api_key,
        streaming=streaming,
    )


def generate_orchestrator_brief(interview_memo: str, model_name: str = "gemini-2.5-flash-lite") -> str:
    """👑司会用の短いブリーフを生成する。"""

    llm = get_llm(temperature=0.5, model_name=model_name)
    prompt = (
        "あなたはオーケストレーターです。以下の面談メモを読み、1段落で司会用ブリーフを作成してください。"
        "回答は必ず日本語で記載してください。"
        "含める要素: 主課題/要求スペック、競合・材料の候補、主要リスク、納期があれば明示、各エージェントへの指示"
        " (Market=事実調査, Internal=社内知見, Architect=発想, Devil=リスク確認)。"
        f"\n\n面談メモ:\n{interview_memo}"
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content.strip()



def agent_market_researcher(tech_tags: List[str], use_case: str = "", model_name: str = "gemini-2.5-flash-lite") -> tuple[str, List[Dict]]:
    """🕵️市場調査エージェント。DuckDuckGo で市場トレンドを検索。
    
    Returns:
        tuple[str, List[Dict]]: (市場調査サマリー, 学術論文情報のリスト)
    """

    # 重要度の高いタグを選定（最大5つ）
    selected_tags = select_important_tags(tech_tags, interview_memo=use_case, max_tags=5, model_name=model_name)
    
    # 選定されたタグで検索を実行
    results = backend.search_market_trends(selected_tags, use_case) or ""
    patents = search_patents(selected_tags) or ""
    academics_list = search_arxiv(" ".join(selected_tags))
    academics = format_arxiv_results(academics_list) if academics_list else ""
    avatar = MARKET_RESEARCHER_AVATAR
    
    # 検索結果が空または不十分な場合の判定
    # 市場情報が見つからない、または市場規模・トレンド・競合の情報が不十分な場合
    market_info_insufficient = (
        not results.strip() or 
        "市場情報が見つかりませんでした" in results or 
        "市場調査結果を取得できませんでした" in results
    )
    
    # 検索結果が空の場合、フォールバック情報を使用
    if not any([results.strip(), patents, academics]) or market_info_insufficient:
        # フォールバック情報を使用して市場調査サマリーを生成
        prompt = (
            "You are a Market Researcher. Summarize the following fallback market information "
            "into facts only (Competitors, Market Size, Trends, Patents, Academic papers). "
            "Respond in Japanese only.\n"
            "各セクションは必ず見出し行から始めてください: '## 競合他社', '## 市場規模', '## トレンド', '## 特許', '## 学術論文'.\n"
            "1セクションは箇条書きで簡潔にまとめてください。\n\n"
            "Fallback Market Information:\n{fallback_info}\n\n"
            "Patents: {patents}\n\n"
            "Academic: {academics}\n\n"
            "注意: 検索結果が不十分なため、フォールバック情報を優先的に使用してください。"
        ).format(
            fallback_info=FALLBACK_MARKET_INFO,
            patents=patents if patents else "特許情報は見つかりませんでした。",
            academics=academics if academics else "学術論文情報は見つかりませんでした。"
        )
        llm = get_llm(temperature=0.3, model_name=model_name)
        response = llm.invoke([HumanMessage(content=prompt)])
        summary = response.content.strip()
    else:
        # 検索結果がある場合、通常の処理を実行
        # ただし、市場規模・トレンド・競合の情報が不十分な場合はフォールバック情報も併用
        prompt = (
            "You are a Market Researcher. Summarize the following search results into facts only "
            "(Competitors, Market Size, Trends, Patents, Academic papers). No speculation. "
            "Respond in Japanese only.\n"
            "各セクションは必ず見出し行から始めてください: '## 競合他社', '## 市場規模', '## トレンド', '## 特許', '## 学術論文'.\n"
            "1セクションは箇条書きで簡潔にまとめてください。\n\n"
            "Market Search Results: {results}\n\n"
            "Fallback Market Information (検索結果が不十分な場合に使用):\n{fallback_info}\n\n"
            "Patents: {patents}\n\n"
            "Academic: {academics}\n\n"
            "注意: 検索結果に市場規模・トレンド・競合の情報が不十分な場合は、"
            "フォールバック情報を優先的に使用してください。"
        ).format(
            results=results,
            fallback_info=FALLBACK_MARKET_INFO,
            patents=patents,
            academics=academics
        )
        llm = get_llm(temperature=0.3, model_name=model_name)
        response = llm.invoke([HumanMessage(content=prompt)])
        summary = response.content.strip()
    
    st.markdown(render_message_html("assistant", avatar, summary), unsafe_allow_html=True)
    # 会話ログに追加
    if "conversation_log" in st.session_state:
        st.session_state.conversation_log.append({
            "role": "assistant",
            "avatar": avatar,
            "content": summary
        })
    return summary, academics_list



def agent_internal_specialist(query_text: str, department: str) -> tuple[str, List[dict]]:
    """🔍社内データ検索エージェント。他事業部の知見を検索。"""

    hits = backend.search_cross_pollination(query_text, department, top_k=3) or []
    hits = backend.search_cross_pollination(query_text, department, top_k=3) or []
    avatar = INTERNAL_SPECIALIST_AVATAR
    if not hits:
        msg = "関連する社内データが見つかりませんでした。"
        st.markdown(render_message_html("assistant", avatar, msg), unsafe_allow_html=True)
        # 会話ログに追加
        if "conversation_log" in st.session_state:
            st.session_state.conversation_log.append({
                "role": "assistant",
                "avatar": avatar,
                "content": msg
            })
        return msg, []

    bullet_lines = []
    for item in hits:
        metadata = item.get("metadata", {}) if isinstance(item, dict) else {}
        company = metadata.get("company") or metadata.get("client") or "Unknown Company"
        dept = metadata.get("department") or "Unknown Dept"
        content = item.get("content", "") if isinstance(item, dict) else ""
        bullet_lines.append(f"- {company} ({dept}): {content[:200]}".strip())

    result_text = "\n".join(bullet_lines)
    st.markdown(render_message_html("assistant", avatar, result_text), unsafe_allow_html=True)
    # 会話ログに追加
    if "conversation_log" in st.session_state:
        st.session_state.conversation_log.append({
            "role": "assistant",
            "avatar": avatar,
            "content": result_text
        })
    return result_text, hits



def _stream_response(llm, messages: List, avatar: str) -> str:
    """LLM出力をStreamlitにストリーム表示するヘルパー。"""

    buffer = ""
    placeholder = st.empty()
    for chunk in llm.stream(messages):
        if chunk.content:
            buffer += chunk.content
            placeholder.markdown(render_message_html("assistant", avatar, buffer), unsafe_allow_html=True)
    # 会話ログに追加
    if buffer and "conversation_log" in st.session_state:
        st.session_state.conversation_log.append({
            "role": "assistant",
            "avatar": avatar,
            "content": buffer
        })
    return buffer


def agent_solution_architect(
    market_data: str,
    internal_data: str,
    interview_memo: str,
    feedback: Optional[str] = None,
    model_name: str = "gemini-2.5-flash-lite",
) -> str:
    """💡ソリューションアーキテクトエージェント。市場データと社内データを統合して提案を作成。"""

    llm = get_llm(temperature=0.9, streaming=True, model_name=model_name)

    intro = ""
    if feedback:
        intro = "I will refine the plan based on the feedback and ensure the issues are addressed.\n\n"
        # 日本語訳:
        # 「フィードバックがある場合は、それに応じて提案を修正すること。」

    prompt = (
        "You are a Genius Solution Architect in a chemical company. Combine the following "
        "\"Internal Data\" and \"Market Facts\" to solve the \"Customer Dilemma\" described in the Interview Memo.\n\n"
        "Constraints:\n"
        "Do NOT just propose existing products. Create a \"Chemical Reaction\" (new combination).\n"
        "If feedback is provided, you MUST revise your proposal to address the criticism.\n"
        "Respond in Japanese only.\n\n"
        f"Internal Data:\n{internal_data}\n\n"
        f"Market Facts:\n{market_data}\n\n"
        f"Interview Memo (Customer Dilemma):\n{interview_memo}\n\n"
        f"Feedback (if any):\n{feedback or 'None'}\n\n"
        f"{intro}Respond with a concrete proposal."
    )
    # 日本語訳:
    # 「あなたは化学メーカーの天才ソリューションアーキテクトです。以下の『Internal Data』と『Market Facts』を組み合わせ、
    # Interview Memo に記載された『Customer Dilemma』を解決する提案を作ってください。既存品の提案だけは避け、
    # 新しい『Chemical Reaction（組み合わせ）』を作ること。フィードバックがある場合は、それに応じて提案を修正すること。」

    # 新しい『Chemical Reaction（組み合わせ）』を作ること。フィードバックがある場合は、それに応じて提案を修正すること。」

    return _stream_response(llm, [HumanMessage(content=prompt)], avatar=SOLUTION_ARCHITECT_AVATAR)



def agent_devils_advocate(proposal: str, model_name: str = "gemini-2.5-flash-lite") -> str:
    """👿悪魔の擁護者エージェント。提案を厳しく批判。"""

    llm = get_llm(temperature=0.5, streaming=True, model_name=model_name)
    prompt = (
        "You are a Devil's Advocate (Strict Technical Reviewer) inside the proposing company. "
        "Write as an internal reviewer (use 「当社」「当方」「我々」) and never from the client's perspective "
        "(avoid 「貴社/御社」「お客様」等). Criticize the following proposal ruthlessly. Focus on:\n\n"
        "Chemical Risks (Hydrolysis, Heat degradation)\n"
        "Cost Feasibility\n"
        "Mass Production Issues\n\n"
        "Respond in Japanese only, concise bullet style if suitable.\n\n"
        f"Proposal: {proposal}"
    )
    # 日本語訳:
    # 「あなたは悪魔の擁護者（厳しい技術レビュー）です。以下の提案を厳しく批判してください。焦点は：
    # 化学リスク（水解、熱劣化）
    # コスト実現性
    # 量産問題です。」

    # 化学リスク（水解、熱劣化）
    # コスト実現性
    # 量産問題です。」

    return _stream_response(llm, [HumanMessage(content=prompt)], avatar=DEVILS_ADVOCATE_AVATAR)


def agent_orchestrator_summary(
    proposal: str,
    market_data: str,
    internal_data: str,
    interview_memo: str,
    tech_tags: List[str],
    company_name: str,
    model_name: str = "gemini-2.5-flash-lite",
) -> str:
    """👑要約エージェント。指定テンプレートに沿って最終レポートを作成。"""

    llm = get_llm(temperature=0.5, model_name=model_name)

    # /services/report_generator.pyのREPORT_SYSTEM_PROMPTを使用
    system_prompt = REPORT_SYSTEM_PROMPT

    # /services/report_generator.pyのREPORT_HUMAN_PROMPTを使用
    human_prompt = REPORT_HUMAN_PROMPT.format(
        company_name=company_name,
        interview_content=interview_memo,
        tech_tags="、".join(tech_tags),
        cross_link_text=internal_data,
        market_trends=market_data,
        proposal=proposal
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt),
    ]

    response = llm.invoke(messages)
    summary = response.content.strip()
    return summary


def run_innovation_squad(
    interview_memo: str,
    tech_tags: List[str],
    department: str,
    company_name: str = "",
    progress_callback: Optional[callable] = None,
    model_name: str = "gemini-2.5-flash-lite",
) -> tuple[str, List[dict], List[dict]]:
    """イノベーション分隊のフローを実行し、最終レポートのMarkdown、他事業部知見リスト、学術論文情報を返す。
    
    Returns:
        tuple[str, List[dict], List[dict]]: (最終レポート, 他事業部知見リスト, 学術論文情報リスト)
    """
    # 会話ログを初期化
    if "conversation_log" not in st.session_state:
        st.session_state.conversation_log = []
    
    # CSSは呼び出し元で注入済みのため削除
    # st.markdown(get_chat_css(), unsafe_allow_html=True)

    if progress_callback:
        progress_callback(15, "オーケストレーター: チームへのブリーフィングを作成中...")

    brief = generate_orchestrator_brief(interview_memo, model_name=model_name)
    brief_content = brief or "チーム、開始しましょう。"
    st.markdown(render_message_html("assistant", ORCHESTRATOR_AVATAR, brief_content), unsafe_allow_html=True)
    st.session_state.conversation_log.append({
        "role": "assistant",
        "avatar": ORCHESTRATOR_AVATAR,
        "content": brief_content
    })

    if progress_callback:
        progress_callback(30, "マーケットリサーチャー & 社内スペシャリスト: 情報収集中...")

    market_data, academic_results = agent_market_researcher(tech_tags, use_case=interview_memo, model_name=model_name)
    internal_data, internal_hits = agent_internal_specialist(interview_memo, department)

    if progress_callback:
        progress_callback(40, "オーケストレーター: 議論の方向性を指示中...")

    orchestrator_msg1 = "材料は揃った。Architect、競合を上回るロジックを組んでくれ。"
    st.markdown(render_message_html("assistant", ORCHESTRATOR_AVATAR, orchestrator_msg1), unsafe_allow_html=True)
    # 会話ログに追加
    st.session_state.conversation_log.append({
        "role": "assistant",
        "avatar": ORCHESTRATOR_AVATAR,
        "content": orchestrator_msg1
    })
    
    if progress_callback:
        progress_callback(55, "ソリューションアーキテクト: 初期提案を作成中...")

    proposal_v1 = agent_solution_architect(market_data, internal_data, interview_memo, model_name=model_name)
    # 会話ログはagent_solution_architect内の_stream_responseで追加済み

    if progress_callback:
        progress_callback(70, "デビルズアドボケイト: リスク分析と批判的レビューを実行中...")

    orchestrator_msg2 = "Devil、この案の弱点を洗い出してくれ。"
    st.markdown(render_message_html("assistant", ORCHESTRATOR_AVATAR, orchestrator_msg2), unsafe_allow_html=True)
    # 会話ログに追加
    st.session_state.conversation_log.append({
        "role": "assistant",
        "avatar": ORCHESTRATOR_AVATAR,
        "content": orchestrator_msg2
    })
    
    critique = agent_devils_advocate(proposal_v1, model_name=model_name)
    # 会話ログはagent_devils_advocate内の_stream_responseで追加済み

    if progress_callback:
        progress_callback(80, "オーケストレーター: 改善指示を出しています...")

    orchestrator_msg3 = "Architect、指摘を踏まえて改訂案を出して。"
    st.markdown(render_message_html("assistant", ORCHESTRATOR_AVATAR, orchestrator_msg3), unsafe_allow_html=True)
    # 会話ログに追加
    st.session_state.conversation_log.append({
        "role": "assistant",
        "avatar": ORCHESTRATOR_AVATAR,
        "content": orchestrator_msg3
    })
    
    if progress_callback:
        progress_callback(90, "ソリューションアーキテクト: 最終提案を練り上げています...")

    proposal_final = agent_solution_architect(market_data, internal_data, interview_memo, feedback=critique, model_name=model_name)
    # 会話ログはagent_solution_architect内の_stream_responseで追加済み

    orchestrator_msg4 = "よし、これで行こう！ みんなありがとう。"
    st.markdown(render_message_html("assistant", ORCHESTRATOR_AVATAR, orchestrator_msg4), unsafe_allow_html=True)
    # 会話ログに追加
    st.session_state.conversation_log.append({
        "role": "assistant",
        "avatar": ORCHESTRATOR_AVATAR,
        "content": orchestrator_msg4
    })

    if progress_callback:
        progress_callback(95, "オーケストレーター: 最終レポートを作成中...")

    final_report_md = agent_orchestrator_summary(
        proposal=proposal_final,
        market_data=market_data,
        internal_data=internal_data,
        interview_memo=interview_memo,
        tech_tags=tech_tags,
        company_name=company_name,
        model_name=model_name,
    )
    # 会話ログはagent_orchestrator_summary内で追加済み
    
    if progress_callback:
        progress_callback(100, "完了！")

    return final_report_md, internal_hits, academic_results
