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
        /* タブの中身をビューポート内でスクロール可能にする */
        [data-testid="stTabs"] [role="tabpanel"] > div {
            max-height: calc(100vh - 230px);
            overflow-y: auto;
            padding-right: 12px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    
    # セッションステートの初期化
    init_session_state()
    
    # サイドバー
    with st.sidebar:
        selected_department, api_keys_ok, form_data = render_sidebar()
    
    # メインコンテンツ
    if not api_keys_ok:
        st.warning("⚠️ APIキーが設定されていないため、機能を利用できません。")
        return
    
    # タブを作成
    tab1, tab2, tab3 = st.tabs([
        "🤖 AIレビュー結果",
        "💬 イノベーション分隊の会話ログ",
        "💡 アイデア創出レポート"
    ])

    # 会話ログは専用タブのコンテナを使って描画する
    with tab2:
        conversation_container = st.container()
    
    # タブ1: AIレビュー結果（会話ログ出力先を渡す）
    with tab1:
        render_review_results(selected_department, conversation_container)
    
    # タブ2: イノベーション分隊の会話ログ
    with tab2:
        render_conversation_log(conversation_container)
    
    # タブ3: アイデア創出レポート
    with tab3:
        render_idea_report()


if __name__ == "__main__":
    main()
