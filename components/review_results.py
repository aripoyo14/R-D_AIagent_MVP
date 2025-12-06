"""
AIレビュー結果表示コンポーネント
"""

import streamlit as st
from services.ai_review import ReviewResult
from services.multi_agent import run_innovation_squad
from backend import save_interview_note
from datetime import datetime
from typing import Optional

try:
    from google.api_core import exceptions as google_exceptions
except Exception:  # ランタイム環境によっては import できない場合がある
    google_exceptions = None


from components.conversation_log import get_chat_css

def handle_registration(
    selected_department: str,
    review: ReviewResult,
    conversation_container: Optional[st.delta_generator.DeltaGenerator] = None,
    progress_container: Optional[st.delta_generator.DeltaGenerator] = None,
    model_name: str = "gemini-2.5-flash-lite",
):
    """
    登録処理とアイデア創出プロセスを実行する
    
    Args:
        selected_department: 選択された事業部名
        review: AIレビュー結果
        conversation_container: 会話ログタブに配置したコンテナ（スピナー表示用）
        progress_container: プログレスバーを表示するコンテナ
        model_name: 使用するAIモデル名
    """
    # メタデータを準備
    metadata = {
        "company_name": st.session_state.form_data.get("company_name", ""),
        "contact_info": st.session_state.form_data.get("contact_info", ""),
        "department": selected_department,
        "tech_tags": review.tech_tags,
        "created_at": datetime.now().isoformat()
    }
    
    # 保存
    with st.spinner("💾 データを保存中..."):
        success = save_interview_note(
            text=st.session_state.form_data.get("interview_memo", ""),
            metadata=metadata
        )
    
    if success:
        st.success("✅ データが正常に保存されました！")
        st.balloons()

        # アイデア創出プロセスを実行
        target_container = conversation_container or st
        with target_container:
            try:
                # LINE風チャットUIのCSSを注入（コンテナ作成前に適用）
                st.markdown(get_chat_css(), unsafe_allow_html=True)

                # カスタムレイアウトで進捗を表示
                status_text_area = st.empty()
                progress_bar = st.progress(0)
                
                # 詳細ログ用のExpander（最初は閉じておく）
                with st.expander("詳細ログを表示", expanded=False):
                    log_area = st.empty()
                    logs = []

                # 会話ログ用のスクロール可能なコンテナを作成
                # Streamlit 1.30.0以上で height パラメータが使用可能
                try:
                    chat_log_container = st.container(height=330, border=False)
                    # このコンテナがある時だけ、親のタブパネルのスクロールを無効化するCSS
                    st.markdown("""
                        <style>
                        section[data-testid="stMain"] [data-testid="stTabs"] [role="tabpanel"] > div {
                            overflow-y: hidden !important;
                        }
                        </style>
                    """, unsafe_allow_html=True)
                except TypeError:
                    # 古いバージョンの場合は通常のコンテナ（スクロール機能なし）
                    chat_log_container = st.container()

                # プログレスバーの更新関数
                def update_progress(percent, text):
                    # メインのステータステキスト更新
                    status_text_area.markdown(f"##### 💡 [{percent}%] {text}")
                    # プログレスバー更新
                    progress_bar.progress(percent)
                    
                    # ログに追加
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    logs.append(f"[{timestamp}] {text}")
                    log_area.text("\n".join(logs))
                    
                    if progress_container:
                        with progress_container.container():
                            # プログレスバーの色をプライマリカラー（ボタンの色）に合わせるCSS
                            st.markdown(
                                """
                                <style>
                                div[data-testid="stProgress"] > div > div > div > div {
                                    background-color: #ff4b4b;
                                }
                                </style>
                                """,
                                unsafe_allow_html=True
                            )
                            # st.markdown(f"**{percent}%** {text}")
                            # st.progress(percent)
                            if percent == 100:
                                st.empty()

                # 初期化
                update_progress(0, "チーム結成中...")
                
                interview_content = st.session_state.form_data.get("interview_memo", "")
                
                # 会話ログコンテナの中で実行
                with chat_log_container:
                    idea_report, cross_pollination_results, academic_results = run_innovation_squad(
                        interview_memo=interview_content,
                        tech_tags=review.tech_tags,
                        department=selected_department,
                        company_name=st.session_state.form_data.get("company_name", ""),
                        progress_callback=update_progress,
                        model_name=model_name,
                    )
                
                # 完了時の表示
                status_text_area.success("✅ イノベーション分隊の議論が完了しました！")
                progress_bar.progress(100)
            except Exception as e:
                if "google_exceptions" in globals() and google_exceptions and isinstance(e, google_exceptions.ServiceUnavailable):
                    st.error("⚠️ モデルが混雑しています。少し待ってから再実行してください。")
                else:
                    st.error(f"❌ イノベーション分隊の実行に失敗しました: {e}")
                st.session_state.is_agent_running = False
                return

            # セッションステートに保存
            st.session_state.idea_report = idea_report
            st.session_state.cross_pollination_results = cross_pollination_results
            st.session_state.academic_results = academic_results
            st.session_state.show_idea_report = True

        # フォームデータとレビュー結果は保持（レポート表示のため）
        st.session_state.is_agent_running = False
        st.rerun()
    else:
        st.error("❌ データの保存に失敗しました")
        st.session_state.is_agent_running = False


def render_review_results(
    selected_department: str,
    conversation_container: Optional[st.delta_generator.DeltaGenerator] = None,
    progress_container: Optional[st.delta_generator.DeltaGenerator] = None,
    model_name: str = "gemini-2.5-flash-lite",
):
    """
    AIレビュー結果を表示する

    Args:
        selected_department: 選択された事業部名
        conversation_container: 会話ログタブに配置したコンテナ（スピナー表示用）
        progress_container: プログレスバーを表示するコンテナ
        model_name: 使用するAIモデル名
    """
    # レイアウト幅を広めに確保（チャットやレポートを読みやすくするため）
    st.markdown(
        """
        <style>
        div.block-container {max-width: 1200px !important;}
        div[data-testid="chat-message"] {max-width: 100% !important;}
        </style>
        """,
        unsafe_allow_html=True,
    )
    if not st.session_state.review_result:
        return
    
    st.header("🤖 AIレビュー結果")
    
    review = st.session_state.review_result
    
    if review.is_sufficient:
        # 情報が十分な場合
        st.success("✅ 情報が十分です。登録可能な状態です。")
        
        # 要約を表示
        if review.summary:
            st.subheader("📋 内容要約")
            st.info(review.summary)
        
        # 技術タグを表示
        if review.tech_tags:
            st.subheader("🏷️ 抽出された技術タグ")
            tags_display = " ".join([f"`{tag}`" for tag in review.tech_tags])
            st.markdown(tags_display)
        
        # 登録ボタン
        if "is_agent_running" not in st.session_state:
            st.session_state.is_agent_running = False

        st.divider()
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            register_clicked = st.button(
                "この内容で登録しますか？",
                type="primary",
                use_container_width=True,
                disabled=st.session_state.is_agent_running,
            )

        if register_clicked:
            st.session_state.is_agent_running = True
            handle_registration(selected_department, review, conversation_container, progress_container, model_name=model_name)
    else:
        # 情報が不足している場合
        st.warning("⚠️ 情報が不足しています。以下の点について確認してください。")
        
        if review.questions:
            st.subheader("❓ 追加で確認すべき質問")
            for i, question in enumerate(review.questions, 1):
                st.markdown(f"{i}. {question}")
        
        st.info("💡 具体的な数値や、現行品の問題点などを追加で記入してください。")
