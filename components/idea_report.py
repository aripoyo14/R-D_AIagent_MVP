"""
アイデア創出レポート表示コンポーネント
"""

import streamlit as st
from typing import List, Dict
from services.markdown_parser import parse_markdown_to_slides
from services.html_report import create_html_report
from services.slide_report import create_slide_report


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
    
    # HTMLレポート出力ボタン
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("📄 HTMLで保存", type="primary", use_container_width=True):
            try:
                with st.spinner("HTMLレポートを生成中..."):
                    company_name = st.session_state.form_data.get("company_name", "")
                    slides_data = parse_markdown_to_slides(
                        st.session_state.idea_report,
                        company_name=company_name
                    )
                    html_path = create_html_report(
                        slides_data,
                        title="アイデア創出レポート",
                        company_name=company_name,
                    )
                    st.success("✅ HTMLレポートを作成しました")
                    st.markdown(f"[ローカルで開く]({html_path})")
                    st.session_state.html_report_path = html_path
            except ValueError as e:
                st.error(f"❌ 設定エラー: {str(e)}")
            except Exception as e:
                st.error(f"❌ エラーが発生しました: {str(e)}")

    with col3:
        if st.button("📊 スライドを作成", type="primary", use_container_width=True):
            try:
                with st.spinner("スライドを生成中..."):
                    company_name = st.session_state.form_data.get("company_name", "")
                    slides_data = parse_markdown_to_slides(
                        st.session_state.idea_report,
                        company_name=company_name
                    )
                    slide_path = create_slide_report(
                        slides_data,
                        title="アイデア創出レポート",
                        company_name=company_name,
                    )
                    st.success("✅ スライドを作成しました")
                    st.markdown(f"[スライドを開く]({slide_path})")
                    st.session_state.slide_report_path = slide_path
            except ValueError as e:
                st.error(f"❌ 設定エラー: {str(e)}")
            except Exception as e:
                st.error(f"❌ エラーが発生しました: {str(e)}")
    
    # 以前に作成されたレポートへのリンク
    if hasattr(st.session_state, 'html_report_path') and st.session_state.html_report_path:
        st.info(f"📎 作成済みレポート: [開く]({st.session_state.html_report_path})")
    
    if hasattr(st.session_state, 'slide_report_path') and st.session_state.slide_report_path:
        st.info(f"📎 作成済みスライド: [開く]({st.session_state.slide_report_path})")
    
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
