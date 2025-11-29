"""
DuckDuckGoを使用した業界ニュース検索サービス
"""
from ddgs import DDGS
from typing import List

def search_industry_news(keywords: List[str], company_name: str = "") -> str:
    """
    業界ニュースやプレスリリースを検索します。
    
    Args:
        keywords: 技術キーワードのリスト
        company_name: 検索に含める企業名（オプション）
        
    Returns:
        str: 検索結果（テキスト）
    """
    try:
        # クエリの構築
        # 例: "ポリマー 耐熱性 (news OR ニュース OR プレスリリース OR 新製品) 2024 2025"
        tags_str = " ".join(keywords)
        
        base_query = f"{tags_str} (news OR ニュース OR プレスリリース OR 新製品) 2024 2025"
        
        if company_name:
            query = f"{company_name} {base_query}"
        else:
            query = f"化学業界 {base_query}"
            
        results_list = []
        with DDGS() as ddgs:
            # text()メソッドを使用して検索
            for r in ddgs.text(query, max_results=5):
                results_list.append(f"Title: {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}\n")
        
        if not results_list:
            return "ニュースは見つかりませんでした。"
            
        return "\n".join(results_list)
    except Exception as e:
        return f"ニュース検索エラー: {str(e)}"
