"""
R&D Brain - Backend Module
Supabaseとの接続とベクトル検索機能を提供
"""

import streamlit as st
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_community.tools import DuckDuckGoSearchRun
from supabase import create_client, Client
from typing import List, Dict, Optional
import json
import os
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()


def init_vector_store() -> SupabaseVectorStore:
    """
    LangChainのSupabaseVectorStoreを初期化する
    
    Returns:
        SupabaseVectorStore: 初期化されたベクトルストア
    """
    # 環境変数から設定を取得
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    # Supabaseクライアントを作成
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # Embeddingモデルを初期化
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=openai_api_key
    )
    
    # SupabaseVectorStoreを初期化
    vector_store = SupabaseVectorStore(
        client=supabase,
        embedding=embeddings,
        table_name="documents",
        query_name="match_documents"
    )
    
    return vector_store


def get_supabase_client() -> Client:
    """
    Supabaseクライアントを取得する
    
    Returns:
        Client: Supabaseクライアント
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    return create_client(supabase_url, supabase_key)


def save_interview_note(text: str, metadata: Dict) -> bool:
    """
    面談内容をEmbedding化してSupabaseに保存する
    
    Args:
        text: 面談内容のテキスト
        metadata: メタデータ（企業名、役職、事業部、技術タグ、登録日時など）
    
    Returns:
        bool: 保存成功時True
    """
    try:
        # Embeddingモデルを初期化
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # テキストをEmbedding化
        embedding = embeddings.embed_query(text)
        
        # メタデータに登録日時を追加（まだない場合）
        if "created_at" not in metadata:
            from datetime import datetime
            metadata["created_at"] = datetime.now().isoformat()
        
        # Supabaseクライアントを取得
        supabase = get_supabase_client()
        
        # 直接Supabaseに挿入（IDはBIGSERIALで自動生成される）
        response = supabase.table("documents").insert({
            "content": text,
            "metadata": metadata,
            "embedding": embedding
        }).execute()
        
        return True
    except Exception as e:
        st.error(f"データ保存エラー: {str(e)}")
        return False


def search_cross_pollination(query_text: str, current_department: str, top_k: int = 5) -> List[Dict]:
    """
    他事業部の知見を検索する（現在の事業部と異なるもののみ）
    
    Args:
        query_text: 検索クエリテキスト
        current_department: 現在の事業部名
        top_k: 取得する結果の数（デフォルト: 5）
    
    Returns:
        List[Dict]: 検索結果のリスト（各要素はid, content, metadata, similarityを含む）
    """
    try:
        # クエリのEmbeddingを取得
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        query_embedding = embeddings.embed_query(query_text)
        
        # Supabaseクライアントを取得
        supabase = get_supabase_client()
        
        # match_documents関数を呼び出し（フィルタなしで全件取得）
        # その後、Python側でdepartment != current_departmentでフィルタリング
        response = supabase.rpc(
            "match_documents",
            {
                "query_embedding": query_embedding,
                "match_threshold": 0.0,  # 閾値は低めに設定（後でフィルタリングするため）
                "match_count": 50,  # 多めに取得してからフィルタリング
                "filter": {}  # フィルタなし
            }
        ).execute()
        
        # 結果を取得
        results = response.data if hasattr(response, 'data') else []
        
        # 現在の事業部と異なるもののみをフィルタリング
        filtered_results = []
        for result in results:
            metadata = result.get("metadata", {})
            department = metadata.get("department", "")
            
            # departmentがcurrent_departmentと異なる場合のみ追加
            if department != current_department:
                filtered_results.append(result)
        
        # similarityでソート（降順）
        filtered_results.sort(key=lambda x: x.get("similarity", 0.0), reverse=True)
        
        # top_k件に制限
        return filtered_results[:top_k]
        
    except Exception as e:
        st.error(f"検索エラー: {str(e)}")
        return []


def search_market_trends(tech_tags: List[str], use_case: str = "") -> str:
    """
    技術タグと用途を元に、最新の市場トレンドを検索する
    
    Args:
        tech_tags: 技術タグのリスト
        use_case: 用途の説明（オプション）
    
    Returns:
        str: 検索結果の要約
    """
    try:
        # 検索クエリを生成
        tags_str = ", ".join(tech_tags)
        if use_case:
            query = f"{tags_str} {use_case} 市場トレンド 規制 新技術 2024 2025"
        else:
            query = f"{tags_str} 市場トレンド 規制 新技術 化学材料 2024 2025"
        
        # DuckDuckGo検索を実行
        search = DuckDuckGoSearchRun()
        results = search.run(query)
        
        return results if results else "市場情報が見つかりませんでした。"
        
    except Exception as e:
        st.warning(f"市場調査エラー: {str(e)}")
        return f"市場調査中にエラーが発生しました: {str(e)}"

