"""
R&D Brain - Main Streamlit Application
営業担当者が面談録を入力し、AIが内容を精査するインターフェース
"""

import streamlit as st
from components import (
    render_sidebar,
    render_review_results,
    render_idea_report,
    render_conversation_log,
    init_session_state
)


def main():
    """メインアプリケーション"""
    st.set_page_config(
        page_title="R&D Brain - 面談録登録",
        page_icon="🧪",
        layout="wide"
    )
    
    st.title("🧪 R&D Brain - 面談録登録システム")
    st.markdown("営業担当者が面談録を入力し、AIが内容を精査します")
    # タブ配下だけをスクロールさせるためのスタイル
    st.markdown(
        """
        <style>
        /* メイン領域全体のスクロールを無効化 */
        section[data-testid="stMain"] {
            overflow: hidden;
        }

        /* メイン領域のタブの中身 */
        section[data-testid="stMain"] [data-testid="stTabs"] [role="tabpanel"] > div {
            height: 63vh;
            overflow-y: auto;
            padding-right: 12px;
            padding-bottom: 20px;
        }
        
        /* サイドバーのタブの中身 */
        section[data-testid="stSidebar"] [data-testid="stTabs"] [role="tabpanel"] > div {
            max-height: 85vh;
            overflow-y: auto;
            padding-right: 12px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    
    # セッションステートの初期化
    init_session_state()
    
    # タブを作成
    tab1, tab2, tab3 = st.tabs([
        "🤖 AIレビュー結果",
        "💬 イノベーション分隊の会話ログ",
        "💡 アイデア創出レポート"
    ])

    # タブ内のコンテナを準備（スピナーや表示位置を固定）
    with tab1:
        review_container = st.container()
    with tab2:
        conversation_container = st.container()
        progress_container = st.empty()
    
    # サイドバー（AIレビューのスピナーをレビュータブに表示するためコンテナを渡す）
    with st.sidebar:
        selected_department, api_keys_ok, form_data, model_name = render_sidebar(review_container)
    
    # メインコンテンツ
    if not api_keys_ok:
        with review_container:
            st.warning("⚠️ APIキーが設定されていないため、機能を利用できません。")
        return
    
    # タブ1: AIレビュー結果（会話ログ出力先を渡す）
    with review_container:
        render_review_results(selected_department, conversation_container, progress_container, model_name=model_name)
    
    # タブ2: イノベーション分隊の会話ログ
    with conversation_container:
        render_conversation_log()
    
    # タブ3: アイデア創出レポート
    with tab3:
        render_idea_report()


if __name__ == "__main__":
    main()
