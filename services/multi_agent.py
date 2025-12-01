"""イノベーション分隊（5エージェント）の中核ロジック。

StreamlitのチャットUIで5人が議論するフローを実装。
プロンプトと進行は仕様に従う。
"""

import os
from typing import List, Optional

import streamlit as st
from langchain_core.messages import HumanMessage, SystemMessage

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None

import backend
from services.patents import search_patents
from services.academic import search_arxiv

from services.report_generator import REPORT_SYSTEM_PROMPT, REPORT_HUMAN_PROMPT


def get_llm(temperature: float = 0.3, streaming: bool = False):
    """LLMを返すファクトリ。Gemini 2.5 Flash を使用。"""

    if ChatGoogleGenerativeAI is None:
        raise ImportError("Gemini を使うには langchain-google-genai のインストールが必要です")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY が設定されていません")

    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=temperature,
        google_api_key=api_key,
        streaming=streaming,
    )


def generate_orchestrator_brief(interview_memo: str) -> str:
    """👑司会用の短いブリーフを生成する。"""

    llm = get_llm(temperature=0.5)
    prompt = (
        "あなたはオーケストレーターです。以下の面談メモを読み、1段落で司会用ブリーフを作成してください。"
        "回答は必ず日本語で記載してください。"
        "含める要素: 主課題/要求スペック、競合・材料の候補、主要リスク、納期があれば明示、各エージェントへの指示"
        " (Market=事実調査, Internal=社内知見, Architect=発想, Devil=リスク確認)。\n\n"
        f"面談メモ:\n{interview_memo}"
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content.strip()



def agent_market_researcher(tech_tags: List[str], use_case: str = "") -> str:
    """🕵️市場調査エージェント。DuckDuckGo で市場トレンドを検索。"""

    results = backend.search_market_trends(tech_tags, use_case) or ""
    patents = search_patents(" ".join(tech_tags)) or ""
    academics = search_arxiv(" ".join(tech_tags)) or ""
    avatar = "🕵️"
    with st.chat_message("assistant", avatar=avatar):
        if not any([results.strip(), patents, academics]):
            st.markdown("No market/patent/academic data found.")
            return "No market/patent/academic data found."

        prompt = (
            "You are a Market Researcher. Summarize the following search results into facts only "
            "(Competitors, Market Size, Trends, Patents, Academic papers). No speculation. "
            "Respond in Japanese only.\n\n"
            "Market: {results}\n\n"
            "Patents: {patents}\n\n"
            "Academic: {academics}"
            # 日本語訳:
            # 「あなたは市場調査エージェントです。以下の検索結果を要約して、競合、市場サイズ、トレンド、特許、論文を事実のみで書いてください。推測はしないでください。」
        ).format(results=results, patents=patents, academics=academics)
        llm = get_llm(temperature=0.3)
        response = llm.invoke([HumanMessage(content=prompt)])
        summary = response.content.strip()
        st.markdown(summary)
        return summary



def agent_internal_specialist(query_text: str, department: str) -> tuple[str, List[dict]]:
    """🔍社内データ検索エージェント。他事業部の知見を検索。"""

    hits = backend.search_cross_pollination(query_text, department, top_k=3) or []
    avatar = "🔍"
    with st.chat_message("assistant", avatar=avatar):
        if not hits:
            msg = "No relevant internal data found."
            st.markdown(msg)
            return msg, []

        bullet_lines = []
        for item in hits:
            metadata = item.get("metadata", {}) if isinstance(item, dict) else {}
            company = metadata.get("company") or metadata.get("client") or "Unknown Company"
            dept = metadata.get("department") or "Unknown Dept"
            content = item.get("content", "") if isinstance(item, dict) else ""
            bullet_lines.append(f"- {company} ({dept}): {content[:200]}".strip())

        result_text = "\n".join(bullet_lines)
        st.markdown(result_text)
        return result_text, hits



def _stream_response(llm, messages: List, avatar: str) -> str:
    """LLM出力をStreamlitにストリーム表示するヘルパー。"""

    buffer = ""
    with st.chat_message("assistant", avatar=avatar):
        placeholder = st.empty()
        for chunk in llm.stream(messages):
            if chunk.content:
                buffer += chunk.content
                placeholder.markdown(buffer)
    return buffer


def agent_solution_architect(
    market_data: str,
    internal_data: str,
    interview_memo: str,
    feedback: Optional[str] = None,
) -> str:
    """💡ソリューションアーキテクトエージェント。市場データと社内データを統合して提案を作成。"""

    llm = get_llm(temperature=0.9, streaming=True)

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

    return _stream_response(llm, [HumanMessage(content=prompt)], avatar="💡")



def agent_devils_advocate(proposal: str) -> str:
    """👿悪魔の擁護者エージェント。提案を厳しく批判。"""

    llm = get_llm(temperature=0.5, streaming=True)
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

    return _stream_response(llm, [HumanMessage(content=prompt)], avatar="👿")


def agent_orchestrator_summary(
    proposal: str,
    market_data: str,
    internal_data: str,
    interview_memo: str,
    tech_tags: List[str],
    company_name: str,
) -> str:
    """👑要約エージェント。指定テンプレートに沿って最終レポートを作成。"""

    llm = get_llm(temperature=0.5)

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
    with st.chat_message("assistant", avatar="🤖"):
        st.markdown(summary)
    return summary


def run_innovation_squad(
    interview_memo: str,
    tech_tags: List[str],
    department: str,
    company_name: str = "",
) -> tuple[str, List[dict]]:
    """イノベーション分隊のフローを実行し、最終レポートのMarkdownと他事業部知見リストを返す。"""

    brief = generate_orchestrator_brief(interview_memo)
    with st.chat_message("assistant", avatar="🤖"):
        st.markdown(brief or "Team, let's start.")

    market_data = agent_market_researcher(tech_tags, use_case=interview_memo)
    internal_data, internal_hits = agent_internal_specialist(interview_memo, department)

    with st.chat_message("assistant", avatar="🤖"):
        st.markdown("材料は揃った。Architect、競合を上回るロジックを組んでくれ。")
    proposal_v1 = agent_solution_architect(market_data, internal_data, interview_memo)

    with st.chat_message("assistant", avatar="🤖"):
        st.markdown("Devil、この案の弱点を洗い出してくれ。")
    critique = agent_devils_advocate(proposal_v1)

    with st.chat_message("assistant", avatar="🤖"):
        st.markdown("Architect、指摘を踏まえて改訂案を出して。")
    proposal_final = agent_solution_architect(market_data, internal_data, interview_memo, feedback=critique)

    final_report_md = agent_orchestrator_summary(
        proposal=proposal_final,
        market_data=market_data,
        internal_data=internal_data,
        interview_memo=interview_memo,
        tech_tags=tech_tags,
        company_name=company_name,
    )
    return final_report_md, internal_hits
