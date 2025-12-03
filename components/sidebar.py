"""
サイドバーコンポーネント
設定とAPIキー確認を表示する
"""

import streamlit as st
import os

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


def render_sidebar():
    """
    サイドバーを表示する
    
    Returns:
        tuple: (選択された事業部名, APIキー設定状況)
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
    
    # デバッグモード設定
    st.subheader("🔍 デバッグ設定")
    debug_patents = st.checkbox(
        "特許検索のデバッグ情報を表示",
        value=st.session_state.get("debug_patents", False),
        help="特許検索の詳細なログと検索結果を表示します"
    )
    st.session_state.debug_patents = debug_patents
    
    return selected_department, api_keys_ok

