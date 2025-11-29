"""
arXivを使用した学術論文検索サービス
"""
import arxiv
from typing import List, Dict

def search_arxiv(query: str, max_results: int = 5) -> List[Dict]:
    """
    arXivで学術論文を検索します。
    
    Args:
        query: 検索クエリ文字列
        max_results: 取得する最大件数
        
    Returns:
        List[Dict]: 論文情報のリスト（タイトル、要約、著者、リンクを含む）
    """
    try:
        # クライアントの構築
        client = arxiv.Client()
        
        # 検索オブジェクトの構築
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )
        
        results = []
        for result in client.results(search):
            results.append({
                "title": result.title,
                "summary": result.summary.replace("\n", " "),
                "authors": [author.name for author in result.authors],
                "link": result.entry_id,
                "published": result.published.strftime("%Y-%m-%d")
            })
            
        return results
    except Exception as e:
        print(f"arXiv検索エラー: {e}")
        return []
