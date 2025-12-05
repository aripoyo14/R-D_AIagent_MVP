"""
イノベーション分隊の会話ログ表示コンポーネント
"""

import streamlit as st


def render_conversation_log():
    """
    イノベーション分隊の会話ログを表示する
    """
    if "conversation_log" not in st.session_state or not st.session_state.conversation_log:
        st.info("💬 イノベーション分隊の会話ログは、面談録を登録した後に表示されます。")
        return
    
    st.header("💬 イノベーション分隊の会話ログ")
    st.markdown("---")
    
    # 会話履歴を表示
    for message in st.session_state.conversation_log:
        avatar = message.get("avatar", "🤖")
        role = message.get("role", "assistant")
        content = message.get("content", "")
        
        with st.chat_message(role, avatar=avatar):
            st.markdown(content)

