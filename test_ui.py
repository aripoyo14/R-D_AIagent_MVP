import streamlit as st
from components.conversation_log import render_conversation_log

# セッションステートの初期化
if "conversation_log" not in st.session_state:
    st.session_state.conversation_log = []

# ダミーデータの投入ボタン
if st.button("ダミーデータを投入"):
    st.session_state.conversation_log = [
        {
            "role": "user",
            "avatar": "👤",
            "content": "新しい化学素材の市場調査をお願いします。"
        },
        {
            "role": "assistant",
            "avatar": "/Users/ayu/create/AgentX2/R-D_AIagent_MVP/images/Orchestrator.png",
            "content": "承知しました。チーム、開始しましょう。"
        },
        {
            "role": "assistant",
            "avatar": "/Users/ayu/create/AgentX2/R-D_AIagent_MVP/images/Market_Researcher.png",
            "content": "市場調査を開始します。競合他社A社が類似特許を出願しています。"
        },
        {
            "role": "assistant",
            "avatar": "/Users/ayu/create/AgentX2/R-D_AIagent_MVP/images/Orchestrator.png",
            "content": "なるほど。ではArchitect、その特許を回避する案を出してくれ。"
        },
        {
            "role": "assistant",
            "avatar": "/Users/ayu/create/AgentX2/R-D_AIagent_MVP/images/Solution_Architect.png",
            "content": "はい。分子構造を少し変更することで回避可能です。\n\n| 項目 | 現行 | 改善案 |\n|---|---|---|\n| 耐熱性 | 200℃ | 250℃ |\n| コスト | 100円 | 120円 |"
        }
    ]

# 会話ログの表示
render_conversation_log()
