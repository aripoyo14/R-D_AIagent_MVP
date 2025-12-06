"""
面談情報入力フォームコンポーネント
"""

import streamlit as st
from services.ai_review import review_interview_content
from typing import Dict
import io
import docx
import pypdf


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
        
        uploaded_file = st.file_uploader(
            "ファイルから読み込む (docx, txt, pdf)",
            type=["docx", "txt", "pdf"],
            key="interview_file_uploader"
        )

        if uploaded_file is not None:
            try:
                text = ""
                if uploaded_file.type == "text/plain":
                    text = uploaded_file.getvalue().decode("utf-8")
                elif uploaded_file.type == "application/pdf":
                    pdf_reader = pypdf.PdfReader(uploaded_file)
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    doc = docx.Document(uploaded_file)
                    for para in doc.paragraphs:
                        text += para.text + "\n"
                
                if text:
                    st.session_state.form_data["interview_memo"] = text
                    # ファイルアップロード後に再実行してテキストエリアを更新
                    # st.rerun() # フォーム内でのrerunは推奨されないため、session_state更新のみに留める
            except Exception as e:
                st.error(f"ファイルの読み込みに失敗しました: {e}")

        # 面談メモはファイルアップロードからのみ取得
        interview_memo = st.session_state.form_data.get("interview_memo", "")
        
        if interview_memo:
            st.success(f"✅ 面談メモを読み込みました ({len(interview_memo)}文字)")
            with st.expander("読み込んだ内容を確認"):
                st.text(interview_memo)
        else:
            st.info("👆 ファイルをアップロードしてください")

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

