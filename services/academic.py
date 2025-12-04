"""
arXivを使用した学術論文検索サービス
"""
import arxiv
import logging
import re
from typing import List, Dict

# ロガーの設定
logger = logging.getLogger(__name__)

# 化学関連のカテゴリ（arXiv）
CHEMISTRY_CATEGORIES = [
    "cond-mat.mtrl-sci",  # 材料科学
    "physics.app-ph",     # 応用物理学
    "cond-mat.soft",      # ソフトマター
    "cond-mat",           # 凝縮系物理学全般
    "physics.chem-ph",    # 化学物理学
]

# 化学関連キーワード（英語）
CHEMISTRY_KEYWORDS = [
    "chemistry", "chemical", "material", "polymer", "molecule", "compound",
    "synthesis", "reaction", "catalyst", "organic", "inorganic", "physical chemistry",
    "materials science", "nanomaterial", "composite", "resin", "polymerization"
]

# 化学に関係ないキーワード（除外用）
NON_CHEMISTRY_KEYWORDS = [
    "betting", "strategy", "gambling", "poker", "casino", "lottery",
    "finance", "economics", "trading", "investment", "stock", "market"
]


def is_chemistry_related(title: str, summary: str) -> bool:
    """
    論文が化学関連かどうかを判定する
    
    Args:
        title: 論文タイトル
        summary: 論文要約
        
    Returns:
        bool: 化学関連の場合True
    """
    text = (title + " " + summary).lower()
    
    # 化学に関係ないキーワードが含まれている場合は除外
    for keyword in NON_CHEMISTRY_KEYWORDS:
        if keyword in text:
            return False
    
    # 化学関連キーワードが含まれている場合はTrue
    for keyword in CHEMISTRY_KEYWORDS:
        if keyword in text:
            return True
    
    # 化学物質名のパターン（例: NH3, CO2, H2Oなど）
    chemical_formula_pattern = r'\b[A-Z][a-z]?\d*[A-Z][a-z]?\d*\b'
    if re.search(chemical_formula_pattern, title + " " + summary):
        return True
    
    # デフォルトはTrue（フィルタリングを緩くする）
    return True


def build_chemistry_query(base_query: str) -> str:
    """
    化学関連の検索クエリを構築する
    
    Args:
        base_query: 元の検索クエリ
        
    Returns:
        str: 化学関連の検索クエリ
    """
    # カテゴリフィルタを追加
    category_filter = " OR ".join([f"cat:{cat}" for cat in CHEMISTRY_CATEGORIES])
    
    # クエリを構築: (元のクエリ) AND (カテゴリフィルタ)
    # より多くの結果を得るために、カテゴリフィルタはOR条件で結合
    query = f"({base_query}) AND ({category_filter})"
    
    return query


def enhance_query_with_chemistry_keywords(query: str) -> str:
    """
    検索クエリに化学関連キーワードを追加する（必要に応じて）
    
    Args:
        query: 元の検索クエリ
        
    Returns:
        str: 強化された検索クエリ
    """
    query_lower = query.lower()
    
    # 既に化学関連キーワードが含まれている場合はそのまま返す
    has_chemistry_keyword = any(keyword in query_lower for keyword in CHEMISTRY_KEYWORDS)
    
    if has_chemistry_keyword:
        return query
    
    # 化学関連キーワードを追加（材料科学、化学を追加）
    enhanced_query = f"{query} (material OR chemistry OR chemical)"
    
    return enhanced_query


def search_arxiv(query: str, max_results: int = 5, chemistry_only: bool = True) -> List[Dict]:
    """
    arXivで学術論文を検索します。
    
    Args:
        query: 検索クエリ文字列
        max_results: 取得する最大件数
        chemistry_only: 化学関連の論文のみを返すか（デフォルト: True）
        
    Returns:
        List[Dict]: 論文情報のリスト（タイトル、要約、著者、リンクを含む）
    """
    try:
        logger.info(f"arXiv検索開始: query='{query}', max_results={max_results}, chemistry_only={chemistry_only}")
        
        # クライアントの構築
        client = arxiv.Client()
        
        # 化学関連のクエリを構築
        if chemistry_only:
            # まず化学関連キーワードを追加
            enhanced_query = enhance_query_with_chemistry_keywords(query)
            # カテゴリフィルタを追加
            search_query = build_chemistry_query(enhanced_query)
            logger.info(f"化学関連クエリ: '{search_query}'")
        else:
            search_query = query
        
        # 検索オブジェクトの構築（より多くの結果を取得してからフィルタリング）
        search = arxiv.Search(
            query=search_query,
            max_results=max_results * 5 if chemistry_only else max_results,  # フィルタリング用に多めに取得
            sort_by=arxiv.SortCriterion.Relevance
        )
        
        results = []
        filtered_count = 0
        
        for result in client.results(search):
            title = result.title
            summary = result.summary.replace("\n", " ")
            
            # 化学関連のフィルタリング
            if chemistry_only and not is_chemistry_related(title, summary):
                filtered_count += 1
                continue
            
            results.append({
                "title": title,
                "summary": summary,
                "authors": [author.name for author in result.authors],
                "link": result.entry_id,
                "published": result.published.strftime("%Y-%m-%d"),
                "categories": [cat for cat in result.categories] if hasattr(result, 'categories') else []
            })
            
            # 必要な件数に達したら終了
            if len(results) >= max_results:
                break
        
        if filtered_count > 0:
            logger.info(f"化学に関係ない論文を{filtered_count}件除外しました")
        
        # 結果が0件の場合、カテゴリフィルタを緩和して再試行
        if chemistry_only and len(results) == 0:
            logger.info("結果が0件のため、カテゴリフィルタを緩和して再試行します")
            try:
                enhanced_query = enhance_query_with_chemistry_keywords(query)
                fallback_search = arxiv.Search(
                    query=enhanced_query,
                    max_results=max_results * 3,
                    sort_by=arxiv.SortCriterion.Relevance
                )
                
                for result in client.results(fallback_search):
                    title = result.title
                    summary = result.summary.replace("\n", " ")
                    
                    if not is_chemistry_related(title, summary):
                        continue
                    
                    results.append({
                        "title": title,
                        "summary": summary,
                        "authors": [author.name for author in result.authors],
                        "link": result.entry_id,
                        "published": result.published.strftime("%Y-%m-%d"),
                        "categories": [cat for cat in result.categories] if hasattr(result, 'categories') else []
                    })
                    
                    if len(results) >= max_results:
                        break
            except Exception as fallback_error:
                logger.warning(f"フォールバック検索でもエラー: {fallback_error}")
        
        logger.info(f"arXiv検索完了: {len(results)}件の論文を取得")
        return results
    except Exception as e:
        logger.error(f"arXiv検索エラー: {e}", exc_info=True)
        print(f"arXiv検索エラー: {e}")
        # エラー時はカテゴリフィルタなしで再試行
        if chemistry_only:
            logger.info("カテゴリフィルタなしで再試行します")
            try:
                return search_arxiv(query, max_results, chemistry_only=False)
            except:
                return []
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
