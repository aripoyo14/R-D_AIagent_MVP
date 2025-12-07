"""
サンプルレポート表示コンポーネント
"""

import streamlit as st
import os
import streamlit.components.v1 as components

@st.dialog("スライドプレビュー", width="large")
def preview_slide_modal(html_content: str):
    """
    スライドをモーダルでプレビュー表示する
    """
    components.html(html_content, height=600, scrolling=True)

def render_sample_report():
    """
    サンプルレポートを表示する
    """
    st.header("📑 サンプルレポート")
    
    # 表示するスライドのファイル名リスト
    slide_files = [
        "slide-旭日自動車株式会社-20251206-214751.html",
        "slide-旭日自動車株式会社-20251207-045625.html",
        "slide-旭日自動車株式会社-20251207-053453.html"
    ]
    
    base_dir = os.path.join(os.getcwd(), "outputs")
    
    for slide_file in slide_files:
        file_path = os.path.join(base_dir, slide_file)
        
        # ファイルが存在するか確認
        if not os.path.exists(file_path):
            st.warning(f"ファイルが見つかりません: {slide_file}")
            continue
            
        with st.container():
            col1, col2 = st.columns([3, 1], vertical_alignment="center")
            
            with col1:
                st.markdown(f"#### 📄 {slide_file}")
            
            with col2:
                if st.button("プレビュー", key=f"preview_{slide_file}", type="primary", use_container_width=True):
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            slide_content = f.read()
                        preview_slide_modal(slide_content)
                    except Exception as e:
                        st.error(f"プレビューエラー: {e}")
            
            st.divider()
