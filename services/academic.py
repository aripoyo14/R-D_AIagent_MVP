"""
arXivを使用した学術論文検索サービス
"""
import arxiv
import logging
from typing import List, Dict

# ロガーの設定
logger = logging.getLogger(__name__)

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
        logger.info(f"arXiv検索開始: query='{query}', max_results={max_results}")
        
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
        
        logger.info(f"arXiv検索完了: {len(results)}件の論文を取得")
        return results
    except Exception as e:
        logger.error(f"arXiv検索エラー: {e}", exc_info=True)
        print(f"arXiv検索エラー: {e}")
        return []


def format_arxiv_results(results: List[Dict]) -> str:
    """
    arXiv検索結果を文字列形式にフォーマットします。
    
    Args:
        results: search_arxiv()から返される論文情報のリスト
        
    Returns:
        str: フォーマットされた文字列
    """
    if not results:
        return "学術論文は見つかりませんでした。"
    
    formatted = []
    for i, paper in enumerate(results, 1):
        formatted.append(
            f"論文{i}:\n"
            f"  タイトル: {paper['title']}\n"
            f"  著者: {', '.join(paper['authors'])}\n"
            f"  公開日: {paper['published']}\n"
            f"  リンク: {paper['link']}\n"
            f"  要約: {paper['summary'][:300]}..." if len(paper['summary']) > 300 else f"  要約: {paper['summary']}\n"
        )
    return "\n".join(formatted)
