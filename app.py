"""
R&D Brain - Main Streamlit Application
営業担当者が面談録を入力し、AIが内容を精査するインターフェース
"""

import streamlit as st
from dotenv import load_dotenv
import os

from components import (
    render_sidebar,
    render_review_results,
    render_idea_report,
    render_conversation_log,
    render_sample_report,
    init_session_state
)


def main():
    """メインアプリケーション"""
    # 環境変数を再読み込み（キャッシュ対策）
    load_dotenv(override=True)
    
    st.set_page_config(
        page_title="R&D Brain - 面談録登録",
        page_icon="🧪",
        layout="wide"
    )
    
    st.title("🧪 R&D Brain - 面談録登録システム")
    st.markdown("営業担当者が面談録を入力し、AIが内容を精査します")
    # タブ配下だけをスクロールさせるためのスタイル
    # CSSを定義
    custom_css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;700&family=Roboto:wght@300;400;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
    }
    
    @keyframes glow {
        from {
            text-shadow: 0 0 10px rgba(0, 210, 255, 0.7), 0 0 20px rgba(0, 210, 255, 0.5);
        }
        to {
            text-shadow: 0 0 20px rgba(0, 210, 255, 1.0), 0 0 30px rgba(0, 210, 255, 0.8), 0 0 40px rgba(0, 210, 255, 0.6);
        }
    }

    h1 {
        font-family: 'Orbitron', sans-serif !important;
        letter-spacing: 3px;
        animation: glow 2s ease-in-out infinite alternate;
    }

    h2, h3 {
        font-family: 'Orbitron', sans-serif !important;
        letter-spacing: 2px;
        text-shadow: 0 0 10px rgba(0, 210, 255, 0.5);
    }

    section[data-testid="stMain"] {
        overflow: hidden;
    }

    .stApp {
        background-color: #002060;
        background-image: 
            radial-gradient(circle at 80% 20%, rgba(0, 120, 255, 0.9) 0%, transparent 60%),
            radial-gradient(circle at 20% 80%, rgba(0, 200, 255, 0.7) 0%, transparent 60%);
        background-size: cover, cover;
        background-attachment: fixed;
    }

    section[data-testid="stMain"] [data-testid="stTabs"] [role="tabpanel"] > div {
        height: 63vh;
        overflow-y: auto;
        padding-right: 12px;
        padding-bottom: 20px;
    }
    
    section[data-testid="stSidebar"] {
        background: rgba(10, 15, 30, 0.2);
        backdrop-filter: blur(20px);
        border-right: 3px solid rgba(0, 210, 255, 0.8);
        box-shadow: 5px 0 30px rgba(0, 210, 255, 0.5);
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p {
        color: #e0f7ff !important;
        text-shadow: 0 0 5px rgba(0, 210, 255, 0.5);
    }

    section[data-testid="stSidebar"] [data-testid="stTabs"] [role="tabpanel"] > div {
        max-height: 85vh;
        overflow-y: auto;
        padding-right: 12px;
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)
    
    # セッションステートの初期化
    init_session_state()
    
    # タブを作成
    tab1, tab2, tab3, tab4 = st.tabs([
        "🤖 AIレビュー結果",
        "💬 イノベーション分隊の会話ログ",
        "💡 アイデア創出レポート",
        "📑 サンプルレポート"
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

    # タブ4: サンプルレポート
    with tab4:
        render_sample_report()


if __name__ == "__main__":
    main()
