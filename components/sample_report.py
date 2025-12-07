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
    # Reveal.jsの動作をiframe内で安定させるための設定変更
    # 1. hash: true -> false (URLフラグメントの干渉防止)
    # 2. embedded: true (埋め込みモード有効化)
    # Reveal.jsの動作をiframe内で安定させるための設定変更
    # 1. hash: true -> false (URLフラグメントの干渉防止)
    html_content = html_content.replace("hash: true", "hash: false")
    
    # embeddedモード時はhtml/bodyの高さを明示的に確保しないと表示されない場合があるためCSSを注入
    # また、iframe内でのスクロール競合を防ぐために overflow: hidden を強制
    css_fix = """
    <style>
        html, body, .reveal {
            width: 100%;
            height: 100vh !important;
            margin: 0;
            padding: 0;
            overflow: hidden !important;
        }
    </style>
    """
    if "</head>" in html_content:
        html_content = html_content.replace("</head>", f"{css_fix}\n</head>")
    else:
        html_content = css_fix + html_content
    
    components.html(html_content, height=600, scrolling=False)

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
