import streamlit as st
import time
from components.conversation_log import render_conversation_log, render_message_html

# 定数定義 (services/multi_agent.py からコピーまたはインポート)
ORCHESTRATOR_AVATAR = "/Users/ayu/create/AgentX2/R-D_AIagent_MVP/images/Orchestrator.png"
MARKET_RESEARCHER_AVATAR = "/Users/ayu/create/AgentX2/R-D_AIagent_MVP/images/Market_Researcher.png"
INTERNAL_SPECIALIST_AVATAR = "/Users/ayu/create/AgentX2/R-D_AIagent_MVP/images/Internal_Specialist.png"
SOLUTION_ARCHITECT_AVATAR = "/Users/ayu/create/AgentX2/R-D_AIagent_MVP/images/Solution_Architect.png"
DEVILS_ADVOCATE_AVATAR = "/Users/ayu/create/AgentX2/R-D_AIagent_MVP/images/Devils_Advocate.png"

def main():
    st.set_page_config(page_title="UI Test - R&D Brain", layout="wide")
    st.title("🧪 UI Test Page")

    # セッションステートの初期化
    if "conversation_log" not in st.session_state:
        st.session_state.conversation_log = []

    # レイアウト
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Controls")
        if st.button("▶️ シミュレーション開始", type="primary"):
            run_simulation()
        
        if st.button("🗑️ ログクリア"):
            st.session_state.conversation_log = []
            st.rerun()

    with col2:
        st.subheader("Conversation Log")
        conversation_container = st.container()
        progress_container = st.empty()
        
        with conversation_container:
            render_conversation_log()

def add_log(role, avatar, content):
    st.session_state.conversation_log.append({
        "role": role,
        "avatar": avatar,
        "content": content
    })

def run_simulation():
    st.session_state.conversation_log = []
    progress_container = st.empty()
    conversation_container = st.container()
    
    # プログレスバーの更新関数
    def update_progress(percent, text):
        with progress_container.container():
            # プログレスバーの色をプライマリカラー（ボタンの色）に合わせるCSS
            st.markdown(
                """
                <style>
                div[data-testid="stProgress"] > div > div > div > div {
                    background-color: #ff4b4b;
                }
                </style>
                """,
                unsafe_allow_html=True
            )
            st.markdown(f"**{percent}%** {text}")
            st.progress(percent)
            if percent == 100:
                st.empty()

    # 1. Start
    update_progress(0, "チーム結成中...")
    time.sleep(1)

    # 2. Orchestrator Brief
    update_progress(15, "オーケストレーター: チームへのブリーフィングを作成中...")
    time.sleep(1)
    add_log("assistant", ORCHESTRATOR_AVATAR, "チーム、開始しましょう。今回のターゲットは自動車用軽量素材です。")
    st.rerun() # ログ更新のためリラン（実際はストリーム表示だがテストでは簡易化）

    # Note: st.rerun() するとスクリプトが再実行されるため、
    # 本来はループ内で st.rerun() は使えません（無限ループになるか、状態がリセットされる）。
    # ここでは、st.empty() を使って擬似的に表示を更新するか、
    # 完全にシミュレートするには非同期処理が必要ですが、
    # Streamlitの仕様上、ボタン押下内のループで描画更新を行うのが一般的です。
    
    # 修正: st.rerun() を使わず、直接描画してシミュレートします。
    # ただし、render_conversation_log は session_state を読むので、
    # ここでは簡易的に都度描画を追加していくスタイルにします。
    
    # リセット
    st.session_state.conversation_log = []
    
    with conversation_container:
        # 1. Brief
        update_progress(15, "オーケストレーター: チームへのブリーフィングを作成中...")
        time.sleep(1.0)
        msg1 = "チーム、開始しましょう。今回のターゲットは自動車用軽量素材です。"
        st.markdown(render_message_html("assistant", ORCHESTRATOR_AVATAR, msg1), unsafe_allow_html=True)
        add_log("assistant", ORCHESTRATOR_AVATAR, msg1)
        
        # 2. Research
        update_progress(30, "マーケットリサーチャー & 社内スペシャリスト: 情報収集中...")
        time.sleep(1.5)
        msg2 = "市場調査完了。競合他社は炭素繊維強化プラスチックに注力しています。"
        st.markdown(render_message_html("assistant", MARKET_RESEARCHER_AVATAR, msg2), unsafe_allow_html=True)
        add_log("assistant", MARKET_RESEARCHER_AVATAR, msg2)

        # 3. Direction
        update_progress(40, "オーケストレーター: 議論の方向性を指示中...")
        time.sleep(1.0)
        msg3 = "了解。ではArchitect、コスト面で優位性のある代替案を出してくれ。"
        st.markdown(render_message_html("assistant", ORCHESTRATOR_AVATAR, msg3), unsafe_allow_html=True)
        add_log("assistant", ORCHESTRATOR_AVATAR, msg3)

        # 4. Architect V1
        update_progress(55, "ソリューションアーキテクト: 初期提案を作成中...")
        time.sleep(2.0)
        msg4 = "植物由来のナノセルロース複合材を提案します。\n\n- 軽量かつ高強度\n- コストは炭素繊維の1/3"
        st.markdown(render_message_html("assistant", SOLUTION_ARCHITECT_AVATAR, msg4), unsafe_allow_html=True)
        add_log("assistant", SOLUTION_ARCHITECT_AVATAR, msg4)

        # 5. Devil
        update_progress(70, "デビルズアドボケイト: リスク分析と批判的レビューを実行中...")
        time.sleep(1.5)
        msg5 = "待て。耐水性と耐熱性に懸念がある。自動車エンジンルーム内での使用は厳しいのではないか？"
        st.markdown(render_message_html("assistant", DEVILS_ADVOCATE_AVATAR, msg5), unsafe_allow_html=True)
        add_log("assistant", DEVILS_ADVOCATE_AVATAR, msg5)

        # 6. Redirection
        update_progress(80, "オーケストレーター: 改善指示を出しています...")
        time.sleep(1.0)
        msg6 = "もっともだ。Architect、耐熱性を向上させる添加剤の配合を検討してくれ。"
        st.markdown(render_message_html("assistant", ORCHESTRATOR_AVATAR, msg6), unsafe_allow_html=True)
        add_log("assistant", ORCHESTRATOR_AVATAR, msg6)

        # 7. Architect Final
        update_progress(90, "ソリューションアーキテクト: 最終提案を練り上げています...")
        time.sleep(2.0)
        msg7 = "フッ素系樹脂をコーティングすることで耐熱・耐水を確保する改良案を作成しました。"
        st.markdown(render_message_html("assistant", SOLUTION_ARCHITECT_AVATAR, msg7), unsafe_allow_html=True)
        add_log("assistant", SOLUTION_ARCHITECT_AVATAR, msg7)

        # 8. Report
        update_progress(95, "オーケストレーター: 最終レポートを作成中...")
        time.sleep(1.5)
        
        # 9. Done
        update_progress(100, "完了！")
        time.sleep(0.5)
        st.success("シミュレーション完了")

if __name__ == "__main__":
    main()
