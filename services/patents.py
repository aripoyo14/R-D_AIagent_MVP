"""
DuckDuckGoを使用した特許検索サービス
"""
from ddgs import DDGS
from typing import List, Dict

def search_patents(keywords: List[str], max_results: int = 5) -> str:
    """
    DuckDuckGoを使用してGoogle Patents (site:patents.google.com) から特許を検索します。
    
    Args:
        keywords: 検索キーワードのリスト
        max_results: 取得する最大件数
        
    Returns:
        str: DuckDuckGoからの検索結果（テキスト）
    """
    try:
        # Google Patentsを対象としたクエリの構築
        # 例: "site:patents.google.com polymer heat resistance 2024"
        query_str = " ".join(keywords)
        query = f"site:patents.google.com {query_str} 2024 2025"
        
        results_list = []
        with DDGS() as ddgs:
            # text()メソッドを使用して検索
            for r in ddgs.text(query, max_results=max_results):
                results_list.append(f"Title: {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}\n")
        
        if not results_list:
            return "特許情報は見つかりませんでした。"
            
        return "\n".join(results_list)
    except Exception as e:
        return f"特許検索エラー: {str(e)}"
