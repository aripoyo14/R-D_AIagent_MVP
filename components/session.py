"""
セッションステート管理コンポーネント
"""

import streamlit as st


def init_session_state():
    """セッションステートの初期化"""
    if "review_result" not in st.session_state:
        st.session_state.review_result = None
    if "form_data" not in st.session_state:
        st.session_state.form_data = {}
    if "idea_report" not in st.session_state:
        st.session_state.idea_report = None
    if "show_idea_report" not in st.session_state:
        st.session_state.show_idea_report = False
    if "cross_pollination_results" not in st.session_state:
        st.session_state.cross_pollination_results = []

