"""
R&D Brain - Main Streamlit Application
営業担当者が面談録を入力し、AIが内容を精査するインターフェース
"""

import streamlit as st
from components import (
    render_sidebar,
    render_review_results,
    render_idea_report,
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
    
    # セッションステートの初期化
    init_session_state()
    
    # サイドバー
    with st.sidebar:
        selected_department, api_keys_ok, form_data = render_sidebar()
    
    # メインコンテンツ
    if not api_keys_ok:
        st.warning("⚠️ APIキーが設定されていないため、機能を利用できません。")
        return
    
    # AIレビュー結果の表示
    render_review_results(selected_department)
    
    # アイデア創出レポートの表示
    render_idea_report()


if __name__ == "__main__":
    main()
