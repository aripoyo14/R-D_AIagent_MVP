"""
アイデア創出レポート表示コンポーネント
"""

import streamlit as st
from typing import List, Dict


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


def render_idea_report():
    """
    アイデア創出レポートを表示する
    """
    if not (st.session_state.show_idea_report and st.session_state.idea_report):
        return
    
    st.divider()
    st.header("💡 アイデア創出レポート")
    st.markdown("---")
    
    # レポート本文を表示
    st.markdown(st.session_state.idea_report)
    
    st.divider()
    
    # 他事業部の知見をカード形式で表示
    if st.session_state.cross_pollination_results:
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

