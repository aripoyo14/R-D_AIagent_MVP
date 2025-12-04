# 市場情報の取得方法について

## 概要

本システムでは、市場情報を複数の情報源から取得し、統合して分析しています。市場情報の取得は主に`agent_market_researcher`エージェント（`services/multi_agent.py`）で実行されます。

## 情報源と取得方法

### 1. 市場トレンド検索

**実装場所**: `backend.py`の`search_market_trends`関数

**取得方法**:
- **検索エンジン**: DuckDuckGo（`ddgs`ライブラリ）
- **検索クエリ**: 技術タグ + 用途説明 + "市場トレンド 規制 新技術 2024 2025"
- **取得件数**: 最大5件
- **返却形式**: タイトル、URL、本文スニペットを含むテキスト形式

**コード例**:
```175:208:backend.py
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
        # 検索クエリを生成（面談メモをそのまま入れるとURLが長くなるため整形＋上限）
        tags_str = ", ".join(tech_tags)
        use_case_trimmed = " ".join(use_case.split())[:180] if use_case else ""
        query_parts = [tags_str, use_case_trimmed, "市場トレンド 規制 新技術 2024 2025"]
        query = " ".join([p for p in query_parts if p]).strip()[:512]

        # DuckDuckGo検索を実行（DDGSのtext APIを使用）
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))

        if not results:
            return "市場情報が見つかりませんでした。"

        # シンプルなテキスト整形で返す
        return "\n".join(
            f"{r.get('title', '')} ({r.get('href', '')}) - {r.get('body', '')}"
            for r in results
        )

    except Exception as e:
        st.warning("市場調査エラー: 市場検索に失敗しました。後でもう一度お試しください。")
        return "市場調査結果を取得できませんでした。"
```

### 2. 特許情報検索

**実装場所**: `services/patents.py`の`search_patents`関数

**取得方法**:
- **検索エンジン**: DuckDuckGo（`ddgs`ライブラリ）
- **検索対象**: Google Patents（`site:patents.google.com`）
- **検索クエリ**: 技術キーワード + "2024 2025"
- **取得件数**: 最大5件（デフォルト）
- **返却形式**: タイトル、URL、スニペットを含むテキスト形式

**コード例**:
```7:35:services/patents.py
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
```

### 3. 学術論文検索

**実装場所**: `services/academic.py`の`search_arxiv`関数

**取得方法**:
- **検索API**: arXiv API（`arxiv`ライブラリ）
- **検索クエリ**: 技術キーワードをスペース区切りで結合
- **取得件数**: 最大5件（デフォルト）
- **ソート**: 関連度順（`SortCriterion.Relevance`）
- **返却形式**: 辞書のリスト（タイトル、要約、著者、リンク、公開日を含む）

**コード例**:
```7:42:services/academic.py
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
```

### 4. 業界ニュース検索（参考）

**実装場所**: `services/news.py`の`search_industry_news`関数

**注意**: 現在、`agent_market_researcher`では使用されていませんが、将来的に使用される可能性があります。

**取得方法**:
- **検索エンジン**: DuckDuckGo（`ddgs`ライブラリ）
- **検索クエリ**: 技術キーワード + "(news OR ニュース OR プレスリリース OR 新製品) 2024 2025"
- **取得件数**: 最大5件
- **返却形式**: タイトル、URL、スニペットを含むテキスト形式

## 統合処理

### agent_market_researcher関数

市場情報の取得は`services/multi_agent.py`の`agent_market_researcher`関数で統合されています。

**処理フロー**:
1. `backend.search_market_trends()`で市場トレンドを取得
2. `search_patents()`で特許情報を取得
3. `search_arxiv()`で学術論文を取得
4. 取得した情報をLLM（Gemini 2.5 Flash）に渡して要約
5. 要約結果を返却

**コード例**:
```59:85:services/multi_agent.py
def agent_market_researcher(tech_tags: List[str], use_case: str = "") -> str:
    """🕵️市場調査エージェント。DuckDuckGo で市場トレンドを検索。"""

    results = backend.search_market_trends(tech_tags, use_case) or ""
    patents = search_patents(" ".join(tech_tags)) or ""
    academics = search_arxiv(" ".join(tech_tags)) or ""
    avatar = "🕵️"
    with st.chat_message("assistant", avatar=avatar):
        if not any([results.strip(), patents, academics]):
            st.markdown("No market/patent/academic data found.")
            return "No market/patent/academic data found."

        prompt = (
            "You are a Market Researcher. Summarize the following search results into facts only "
            "(Competitors, Market Size, Trends, Patents, Academic papers). No speculation. "
            "Respond in Japanese only.\n\n"
            "Market: {results}\n\n"
            "Patents: {patents}\n\n"
            "Academic: {academics}"
            # 日本語訳:
            # 「あなたは市場調査エージェントです。以下の検索結果を要約して、競合、市場サイズ、トレンド、特許、論文を事実のみで書いてください。推測はしないでください。」
        ).format(results=results, patents=patents, academics=academics)
        llm = get_llm(temperature=0.3)
        response = llm.invoke([HumanMessage(content=prompt)])
        summary = response.content.strip()
        st.markdown(summary)
        return summary
```

## 依存ライブラリ

市場情報の取得に必要なライブラリ:

- `ddgs` (duckduckgo-search): DuckDuckGo検索用
- `arxiv`: arXiv API用
- `langchain_google_genai`: LLM統合用（Gemini）

## エラーハンドリング

各関数では以下のエラーハンドリングが実装されています:

- **市場トレンド検索**: エラー時は警告メッセージを表示し、空文字列を返す
- **特許検索**: エラー時はエラーメッセージを含む文字列を返す
- **学術論文検索**: エラー時は空のリストを返す

## 今後の改善案

1. **ニュース検索の統合**: `search_industry_news`を`agent_market_researcher`に統合
2. **検索結果のキャッシュ**: 同じクエリの再検索を避けるため、結果をキャッシュ
3. **検索結果の品質向上**: より関連性の高い結果を取得するためのクエリ最適化
4. **追加情報源**: 市場レポート、規制情報、競合分析などの追加情報源の統合

