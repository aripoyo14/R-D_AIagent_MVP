"""
サイドバーコンポーネント
設定とAPIキー確認、面談情報入力を表示する
"""

import streamlit as st
import os
from services.ai_review import review_interview_content
from typing import Dict, Tuple, Optional

# 事業部のリスト
DEPARTMENTS = [
    "エバール事業部",
    "イソプレン事業部",
    "ジェネスタ事業部"
]


def check_api_keys() -> bool:
    """APIキーの設定状況を確認"""
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        has_supabase = supabase_url is not None and supabase_url != "" and supabase_key is not None and supabase_key != ""
        has_openai = openai_api_key is not None and openai_api_key != ""
        return has_supabase and has_openai
    except:
        return False


def render_sidebar(review_container: Optional[st.delta_generator.DeltaGenerator] = None) -> Tuple[str, bool, Dict]:
    """
    サイドバーを表示する
    
    Returns:
        tuple: (選択された事業部名, APIキー設定状況, フォームデータ)
    """
    st.header("⚙️ 設定")
    
    # 事業部選択
    selected_department = st.selectbox(
        "事業部を選択",
        DEPARTMENTS,
        index=0
    )
    
    st.divider()
    
    # APIキー設定状況
    st.subheader("🔑 APIキー設定状況")
    api_keys_ok = check_api_keys()
    if api_keys_ok:
        st.success("✅ すべてのAPIキーが設定されています")
    else:
        st.error("❌ APIキーが設定されていません")
        st.info("環境変数 `SUPABASE_URL`, `SUPABASE_KEY`, `OPENAI_API_KEY` を設定してください")
        
        # デバッグ情報を表示（展開可能なセクション）
        with st.expander("🔍 デバッグ情報（環境変数の確認）"):
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            openai_api_key = os.getenv("OPENAI_API_KEY")
            
            st.write(f"**SUPABASE_URL**: {'✅ 設定済み' if supabase_url else '❌ 未設定'}")
            st.write(f"**SUPABASE_KEY**: {'✅ 設定済み' if supabase_key else '❌ 未設定'}")
            st.write(f"**OPENAI_API_KEY**: {'✅ 設定済み' if openai_api_key else '❌ 未設定'}")
            
            st.info("💡 `.env`ファイルを作成し、`env.example`を参考に環境変数を設定してください。")
    
    st.divider()
    
    # 面談情報入力フォーム
    st.subheader("📝 面談情報入力")
    form_data = render_interview_form(review_container)
    
    return selected_department, api_keys_ok, form_data


def render_interview_form(review_container: Optional[st.delta_generator.DeltaGenerator] = None) -> Dict:
    """
    面談情報入力フォームを表示する
    
    Returns:
        Dict: フォームデータ（company_name, contact_info, interview_memo, submitted）
    """
    with st.form("interview_form", clear_on_submit=False):
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
            height=200,
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
                spinner_target = review_container or st
                with spinner_target:
                    with st.spinner("🤖 AIが内容をレビュー中..."):
                        review_result = review_interview_content(interview_memo)
                        st.session_state.review_result = review_result
    
    return {
        "company_name": company_name,
        "contact_info": contact_info,
        "interview_memo": interview_memo,
        "submitted": submitted
    }
