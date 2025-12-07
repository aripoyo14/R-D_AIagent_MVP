"""
アイデア創出レポート表示コンポーネント
"""

import streamlit as st
import os
from typing import List, Dict
from services.markdown_parser import parse_markdown_to_slides
from services.html_report import create_html_report
from services.slide_report2 import create_slide_report_v2




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
                border: 1px solid rgba(0, 210, 255, 0.3);
                border-radius: 10px;
                padding: 15px;
                margin: 10px 0;
                background-color: rgba(10, 20, 40, 0.6);
                color: #e0f7ff;
            ">
                <h4 style="margin-top: 0; color: #00d2ff; text-shadow: 0 0 5px rgba(0, 210, 255, 0.5);">📋 知見 #{i}</h4>
                <p><strong>企業名:</strong> {metadata.get('company_name', '不明')}</p>
                <p><strong>事業部:</strong> {metadata.get('department', '不明')}</p>
                <p><strong>部署・役職:</strong> {metadata.get('contact_info', '不明')}</p>
                <p><strong>関連度:</strong> <span style="color: #00d2ff; font-weight: bold;">{similarity:.1%}</span></p>
                <p><strong>内容要約:</strong></p>
                <p style="background-color: rgba(0, 0, 0, 0.3); padding: 10px; border-radius: 5px; border: 1px solid rgba(255, 255, 255, 0.1);">{content[:300]}{'...' if len(content) > 300 else ''}</p>
            </div>
            """, unsafe_allow_html=True)


def display_academic_papers(academic_results: List[Dict]):
    """
    学術論文情報をカード形式で表示する
    
    Args:
        academic_results: 学術論文情報のリスト
    """
    if not academic_results:
        st.info("学術論文は見つかりませんでした。")
        return
    
    st.subheader("📚 参考: 関連する学術論文")
    
    for i, paper in enumerate(academic_results, 1):
        title = paper.get("title", "タイトル不明")
        authors = paper.get("authors", [])
        published = paper.get("published", "日付不明")
        link = paper.get("link", "")
        summary = paper.get("summary", "")
        
        with st.container():
            st.markdown(f"""
            <div style="
                border: 1px solid rgba(76, 175, 80, 0.5);
                border-radius: 10px;
                padding: 15px;
                margin: 10px 0;
                background-color: rgba(10, 20, 40, 0.6);
                color: #e0f7ff;
            ">
                <h4 style="margin-top: 0; color: #66bb6a; text-shadow: 0 0 5px rgba(76, 175, 80, 0.5);">📄 論文 #{i}</h4>
                <p><strong>タイトル:</strong> {title}</p>
                <p><strong>著者:</strong> {', '.join(authors[:5])}{'...' if len(authors) > 5 else ''}</p>
                <p><strong>公開日:</strong> {published}</p>
                <p><strong>リンク:</strong> <a href="{link}" target="_blank" style="color: #66bb6a;">{link}</a></p>
                <details>
                    <summary style="cursor: pointer; color: #66bb6a; font-weight: bold;">要約を表示</summary>
                    <p style="background-color: rgba(0, 0, 0, 0.3); padding: 10px; border-radius: 5px; margin-top: 10px; border: 1px solid rgba(255, 255, 255, 0.1);">{summary[:500]}{'...' if len(summary) > 500 else ''}</p>
                </details>
            </div>
            """, unsafe_allow_html=True)


def render_idea_report():
    """
    アイデア創出レポートを表示する
    """
    if not (st.session_state.show_idea_report and st.session_state.idea_report):
        return
    
    # HTMLレポート出力ボタン
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("📊 スライドを作成", type="primary", use_container_width=True):
            try:
                with st.spinner("スライドを生成中..."):
                    company_name = st.session_state.form_data.get("company_name", "")
                    slides_data = parse_markdown_to_slides(
                        st.session_state.idea_report,
                        company_name=company_name
                    )
                    slide_path = create_slide_report_v2(
                        slides_data,
                        title="アイデア創出レポート",
                        company_name=company_name,
                    )
                    st.success("✅ スライドを作成しました")
                    st.session_state.slide_report_path = slide_path
            except ValueError as e:
                st.error(f"❌ 設定エラー: {str(e)}")
            except Exception as e:
                st.error(f"❌ エラーが発生しました: {str(e)}")

    
    
    # 以前に作成されたレポートへのリンク
    if hasattr(st.session_state, 'html_report_path') and st.session_state.html_report_path:
        st.info(f"📎 作成済みレポート: [開く]({st.session_state.html_report_path})")
    
    if hasattr(st.session_state, 'slide_report_path') and st.session_state.slide_report_path:
        # スライドのダウンロードボタンとプレビューボタンを表示
        col_download, col_preview = st.columns([3, 1])
        with col_download:
            try:
                with open(st.session_state.slide_report_path, "r", encoding="utf-8") as f:
                    slide_content = f.read()
                file_name = os.path.basename(st.session_state.slide_report_path)
                st.download_button(
                    label="📥 スライドをダウンロード",
                    data=slide_content,
                    file_name=file_name,
                    mime="text/html",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"ファイル読み込みエラー: {e}")
        
        with col_preview:
            if st.button("プレビュー", key="preview_slide_btn", use_container_width=True):
                try:
                    # 既に読み込んでいる場合は再利用も可能だが、念のため再読み込み（または上のtryブロックで読み込んだ変数を使う）
                    if 'slide_content' not in locals():
                         with open(st.session_state.slide_report_path, "r", encoding="utf-8") as f:
                            slide_content = f.read()
                    preview_slide_modal(slide_content)
                except Exception as e:
                    st.error(f"プレビューエラー: {e}")

    
    # レポート本文を表示
    st.markdown(st.session_state.idea_report)
    
    st.divider()
    
    # 学術論文情報をカード形式で表示
    if hasattr(st.session_state, 'academic_results') and st.session_state.academic_results:
        st.divider()
        display_academic_papers(st.session_state.academic_results)
    
    # 他事業部の知見をカード形式で表示
    if st.session_state.cross_pollination_results:
        st.divider()
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
            if hasattr(st.session_state, 'academic_results'):
                st.session_state.academic_results = []
            st.session_state.show_idea_report = False
            st.rerun()
