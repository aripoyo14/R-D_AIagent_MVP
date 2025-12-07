"""
イノベーション分隊の会話ログ表示コンポーネント
"""

import streamlit as st
import markdown
import base64
import os


def render_conversation_log():
    """
    イノベーション分隊の会話ログを表示する（LINE風UI）
    """
    if "conversation_log" not in st.session_state or not st.session_state.conversation_log:
        st.info("💬 イノベーション分隊の会話ログは、面談録を登録した後に表示されます。")
        return

def get_image_base64(image_path):
    """画像ファイルをBase64エンコードして返す"""
    if not os.path.exists(image_path):
        return None
    with open(image_path, "rb") as f:
        data = f.read()
    encoded = base64.b64encode(data).decode()
    # 拡張子からMIMEタイプを簡易判定
    ext = os.path.splitext(image_path)[1].lower()
    mime = "image/png" if ext == ".png" else "image/jpeg"
    return f"data:{mime};base64,{encoded}"


def get_chat_css():
    """LINE風チャットUIのCSSを返す"""
    return """
    <style>

    /* イノベーション分隊の会話ログ表示コンポーネント */
    .chat-container {
        font-family: "Helvetica Neue", Arial, sans-serif;
        display: flex;
        flex-direction: column;
        gap: 16px;
        padding: 20px;
        background-color: #7494c0 !important; /* LINE風の背景色 */
        border-radius: 12px;
    }

    /* リアルタイム表示用：メッセージを含むコンテナに背景色を適用 */
    [data-testid="stTabs"] [data-testid="stVerticalBlock"]:has(.message-row) {
        background-color: #7494c0 !important;
        padding: 20px;
        border-radius: 12px;
        gap: 16px;
    }
    
    .message-row {
        display: flex;
        align-items: flex-start;
        margin-bottom: 4px;
    }
    
    .message-row.user {
        justify-content: flex-end;
    }
    
    .message-row.assistant {
        justify-content: flex-start;
    }
    
    .avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        background-color: #fff;
        margin-right: 8px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        box_shadow: 0 1px 2px rgba(0,0,0,0.1);
        overflow: hidden; /* 画像がはみ出さないように */
        flex-shrink: 0; /* アイコンが潰れないようにする */
    }
    
    .avatar-image {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    
    .message-bubble {
        max-width: 85%; /* 70% -> 85% に変更 */
        padding: 10px 14px;
        border-radius: 12px;
        position: relative;
        font-size: 14px;
        line-height: 1.5;
        box-shadow: 0 1px 1px rgba(0,0,0,0.1);
        white-space: normal; /* pre-wrapから変更して余白問題を解決 */
    }
    
    /* ユーザー（右側・緑） */
    .message-row.user .message-bubble {
        background-color: #8de055;
        color: #000;
        border-top-right-radius: 0;
    }
    .message-row.user .message-bubble::after {
        content: "";
        position: absolute;
        top: 0;
        right: -6px; /* 隙間対策で少し重ねる */
        width: 0;
        height: 0;
        border-left: 8px solid #8de055;
        border-bottom: 8px solid transparent;
    }
    
    /* オーケストレーター（右側・白・アバターあり） */
    .message-row.orchestrator {
        justify-content: flex-end;
    }
    .message-row.orchestrator .message-bubble {
        background-color: #fff;
        color: #000;
        border-top-right-radius: 0;
        margin-right: 8px; /* アバターとの間隔を少し広げる (2px -> 8px) */
    }
    .message-row.orchestrator .message-bubble::after {
        content: "";
        position: absolute;
        top: 0;
        right: -6px; /* 隙間対策で少し重ねる */
        width: 0;
        height: 0;
        border-left: 8px solid #fff;
        border-bottom: 8px solid transparent;
    }
    .message-row.orchestrator .avatar {
        margin-right: 0;
        margin-left: 0;
    }

    /* アシスタント（左側・白） */
    .message-row.assistant {
        justify-content: flex-start;
    }
    .message-row.assistant .message-bubble {
        background-color: #fff;
        color: #000;
        border-top-left-radius: 0;
    }
    .message-row.assistant .message-bubble::after {
        content: "";
        position: absolute;
        top: 0;
        left: -6px; /* 隙間対策で少し重ねる */
        width: 0;
        height: 0;
        border-right: 8px solid #fff;
        border-bottom: 8px solid transparent;
    }
    
    /* メッセージ内容のラッパー（ロール名と吹き出しをまとめる） */
    .message-content {
        display: flex;
        flex-direction: column;
    }

    .message-row.orchestrator .message-content {
        align-items: flex-end;
    }

    .message-row.assistant .message-content {
        align-items: flex-start;
    }
    
    /* ロール名表示（オプション） */
    .role-name {
        font-size: 10px;
        color: #555;
        margin-bottom: 2px;
        margin-left: 4px;
    }

    /* テーブルのスタイル調整（強力に適用） */
    .message-bubble table {
        margin-bottom: 0 !important;
        width: 100% !important;
        border-collapse: collapse !important;
        font-size: 12px !important;
    }
    .message-bubble thead, .message-bubble tbody, .message-bubble tr {
        border: none !important;
        background: transparent !important;
    }
    .message-bubble th, .message-bubble td {
        padding: 4px 8px !important;
        border: 1px solid #ddd !important;
        line-height: 1.4 !important;
    }
    .message-bubble th {
        background-color: #f2f2f2 !important;
        color: #333 !important;
        font-weight: bold !important;
    }
    /* Markdownの段落マージンを詰める */
    .message-bubble p {
        margin-bottom: 0.2em !important;
    }
    .message-bubble p:last-child {
        margin-bottom: 0 !important;
    }
    </style>
    """


def render_message_html(role, avatar, content):
    """単一メッセージのHTMLを生成する"""
    # MarkdownをHTMLに変換（表と改行をサポート）
    content = markdown.markdown(content, extensions=['tables', 'nl2br'])
    
    # 画像かどうか判定
    is_image = avatar and os.path.exists(avatar)
    
    if is_image:
        img_src = get_image_base64(avatar)
        avatar_html = f'<img src="{img_src}" class="avatar-image">'
    else:
        avatar_html = avatar

    # オーケストレーター判定（絵文字 または ファイル名にOrchestratorが含まれる）
    is_orchestrator = avatar == "👑" or (is_image and "Orchestrator.png" in avatar)

    # ロール名の決定
    role_display = "AI"
    if role == "user":
        role_display = "ユーザー"
    elif is_orchestrator:
        role_display = "オーケストレーター (PM)"
    elif is_image:
        if "Market_Researcher.png" in avatar:
            role_display = "マーケットリサーチャー (外の目)"
        elif "Internal_Specialist.png" in avatar:
            role_display = "インターナルスペシャリスト (社内の情報通)"
        elif "Solution_Architect.png" in avatar:
            role_display = "ソリューションアーキテクト (発明家)"
        elif "Devils_Advocate.png" in avatar:
            role_display = "デビルズアドボケイト (鬼の査読官)"
    
    if role == "user":
        # ユーザーメッセージ（右側）
        return f"""
<div class="message-row user">
    <div class="message-bubble">{content}</div>
</div>
"""
    elif is_orchestrator:
        # オーケストレーター（右側・アバターあり）
        return f"""
<div class="message-row orchestrator">
    <div class="message-content">
        <div class="role-name" style="text-align: right; margin-right: 14px;">{role_display}</div>
        <div class="message-bubble">{content}</div>
    </div>
    <div class="avatar">{avatar_html}</div>
</div>
"""
    else:
        # その他のアシスタント（左側）
        return f"""
<div class="message-row assistant">
    <div class="avatar">{avatar_html}</div>
    <div class="message-content">
        <div class="role-name">{role_display}</div>
        <div class="message-bubble">{content}</div>
    </div>
</div>
"""


def render_conversation_log():
    """
    イノベーション分隊の会話ログを表示する（LINE風UI）
    """
    if "conversation_log" not in st.session_state or not st.session_state.conversation_log:
        st.info("💬 イノベーション分隊の会話ログは、面談録を登録した後に表示されます。")
        return

    # LINE風スタイルの定義
    st.markdown(get_chat_css(), unsafe_allow_html=True)
    
    # チャットログのHTML構築
    html_content = '<div class="chat-container">'
    
    for message in st.session_state.conversation_log:
        avatar = message.get("avatar", "🤖")
        role = message.get("role", "assistant")
        content = message.get("content", "")
        
        html_content += render_message_html(role, avatar, content)
            
    html_content += '</div>'
    
    st.markdown(html_content, unsafe_allow_html=True)

