"""
面談情報入力フォームコンポーネント
"""

import streamlit as st
from services.ai_review import review_interview_content
from typing import Dict


def render_interview_form() -> Dict:
    """
    面談情報入力フォームを表示する
    
    Returns:
        Dict: フォームデータ（company_name, contact_info, interview_memo, submitted）
    """
    with st.form("interview_form", clear_on_submit=False):
        st.header("📝 面談情報入力")
        
        company_name = st.text_input(
            "企業名 (Company Name)",
            value=st.session_state.form_data.get("company_name", ""),
            placeholder="例: トヨタ自動車"
        )
        
        contact_info = st.text_input(
            "相手方 部署・役職",
            value=st.session_state.form_data.get("contact_info", ""),
            placeholder="例: ボディ設計部 課長"
        )
        
        interview_memo = st.text_area(
            "面談メモ (Raw Content)",
            value=st.session_state.form_data.get("interview_memo", ""),
            height=300,
            placeholder="面談の内容を自由に記述してください..."
        )
        
        submitted = st.form_submit_button("AIレビュー実行", type="primary", use_container_width=True)
        
        if submitted:
            if not interview_memo.strip():
                st.error("⚠️ 面談メモを入力してください")
            else:
                # フォームデータを保存
                st.session_state.form_data = {
                    "company_name": company_name,
                    "contact_info": contact_info,
                    "interview_memo": interview_memo
                }
                
                # AIレビューを実行
                with st.spinner("🤖 AIが内容をレビュー中..."):
                    review_result = review_interview_content(interview_memo)
                    st.session_state.review_result = review_result
    
    return {
        "company_name": company_name,
        "contact_info": contact_info,
        "interview_memo": interview_memo,
        "submitted": submitted
    }

