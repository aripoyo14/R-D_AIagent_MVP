# 学術論文検索の実装内容

## 概要

本システムでは、arXiv APIを使用して学術論文を検索する機能を実装しています。この機能は市場調査エージェント（`agent_market_researcher`）の一部として、技術キーワードに関連する最新の学術研究を取得するために使用されます。

## 実装詳細

### ファイル構成

- **実装ファイル**: `services/academic.py`
- **使用箇所**: `services/multi_agent.py`の`agent_market_researcher`関数

### 関数仕様

#### `search_arxiv(query: str, max_results: int = 5) -> List[Dict]`

**目的**: arXivで学術論文を検索し、論文情報を辞書形式で返す

**パラメータ**:
- `query` (str): 検索クエリ文字列（技術キーワードをスペース区切りで結合）
- `max_results` (int): 取得する最大件数（デフォルト: 5）

**戻り値**:
- `List[Dict]`: 論文情報のリスト。各辞書には以下のキーが含まれる:
  - `title` (str): 論文タイトル
  - `summary` (str): 論文要約（改行文字はスペースに置換）
  - `authors` (List[str]): 著者名のリスト
  - `link` (str): 論文のエントリID（URL）
  - `published` (str): 公開日（YYYY-MM-DD形式）

**エラーハンドリング**:
- 例外発生時は`print`でエラーメッセージを出力し、空のリスト`[]`を返す

### 実装コード

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

### 処理フロー

1. **クライアント初期化**: `arxiv.Client()`でarXiv APIクライアントを作成
2. **検索オブジェクト作成**: `arxiv.Search`で検索条件を設定
   - クエリ文字列を指定
   - 最大取得件数を指定
   - ソート順を関連度順（`SortCriterion.Relevance`）に設定
3. **結果取得**: `client.results(search)`で検索結果をイテレート
4. **データ整形**: 各結果から必要な情報を抽出し、辞書形式に変換
   - 要約内の改行文字をスペースに置換
   - 公開日をYYYY-MM-DD形式にフォーマット
5. **返却**: 整形した結果のリストを返す

## 使用例

### 基本的な使用

```python
from services.academic import search_arxiv

# 技術キーワードで検索
results = search_arxiv("polymer heat resistance", max_results=5)

for paper in results:
    print(f"タイトル: {paper['title']}")
    print(f"著者: {', '.join(paper['authors'])}")
    print(f"公開日: {paper['published']}")
    print(f"リンク: {paper['link']}")
    print(f"要約: {paper['summary'][:200]}...")
    print("-" * 80)
```

### マルチエージェントシステムでの使用

`services/multi_agent.py`の`agent_market_researcher`関数で使用されています:

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

**注意**: 現在の実装では、`search_arxiv`の戻り値（`List[Dict]`）を`or ""`で文字列として扱おうとしていますが、これは型の不一致があります。実際には、`List[Dict]`は空でない限り真値として評価されるため、空リストの場合は`or ""`が評価され、空文字列が返されます。

## 依存ライブラリ

### arxiv

**バージョン**: `>=2.1.0`（`requirements.txt`で指定）

**公式ドキュメント**: https://github.com/lukasschwab/arxiv.py

**主な機能**:
- arXiv APIへのアクセス
- 論文検索とメタデータ取得
- 複数のソート基準（関連度、提出日、最終更新日など）

## arXiv APIについて

### 検索クエリの構文

arXiv APIは以下のような検索構文をサポートしています:

- **単純なキーワード**: `polymer`
- **複数キーワード（AND）**: `polymer AND heat`
- **複数キーワード（OR）**: `polymer OR plastic`
- **フレーズ検索**: `"heat resistance"`
- **著者検索**: `au:Smith`
- **タイトル検索**: `ti:polymer`
- **カテゴリ検索**: `cat:cond-mat.mtrl-sci`

### ソート基準

`SortCriterion`で指定可能なソート基準:

- `Relevance`: 関連度順（デフォルトで使用）
- `LastUpdatedDate`: 最終更新日順
- `SubmittedDate`: 提出日順

## データ構造

### 返却される辞書の構造

```python
{
    "title": "論文タイトル",
    "summary": "論文要約（改行なし）",
    "authors": ["著者1", "著者2", ...],
    "link": "https://arxiv.org/abs/1234.5678",
    "published": "2024-01-15"
}
```

### arXiv Resultオブジェクトの主要属性

`client.results(search)`から返される`arxiv.Result`オブジェクトには以下の属性があります:

- `entry_id`: 論文のエントリID（URL）
- `updated`: 最終更新日時（datetime）
- `published`: 公開日時（datetime）
- `title`: タイトル
- `authors`: 著者リスト（`arxiv.Author`オブジェクトのリスト）
- `summary`: 要約
- `comment`: コメント
- `journal_ref`: ジャーナル参照
- `doi`: DOI
- `primary_category`: 主要カテゴリ
- `categories`: カテゴリリスト
- `links`: リンクリスト

## エラーハンドリング

### 現在の実装

```python
try:
    # 検索処理
    ...
    return results
except Exception as e:
    print(f"arXiv検索エラー: {e}")
    return []
```

### 考えられるエラーケース

1. **ネットワークエラー**: arXiv APIへの接続失敗
2. **タイムアウト**: 検索処理が長時間かかる場合
3. **無効なクエリ**: 検索クエリの構文エラー
4. **API制限**: レート制限に達した場合

### 改善案

現在の実装では`print`でエラーを出力していますが、以下の改善が考えられます:

1. **ログ出力**: `logging`モジュールを使用してログレベルを適切に設定
2. **エラーの種類別処理**: ネットワークエラーとAPIエラーを区別
3. **リトライ機能**: 一時的なエラーの場合にリトライ
4. **Streamlit統合**: Streamlitアプリケーション内で使用する場合は`st.error()`を使用

## パフォーマンス

### 検索時間

- 通常の検索: 1-3秒程度
- ネットワーク状況により変動

### 取得件数の制限

- デフォルト: 5件
- 最大件数: arXiv APIの制限に依存（通常は数百件まで可能）

### 最適化のヒント

1. **取得件数の調整**: 必要に応じて`max_results`を調整
2. **クエリの最適化**: より具体的なキーワードを使用して検索精度を向上
3. **キャッシュ**: 同じクエリの再検索を避けるため、結果をキャッシュ

## 既知の問題と制限事項

### 型の不一致

`services/multi_agent.py`の`agent_market_researcher`関数で、`search_arxiv`の戻り値（`List[Dict]`）を文字列として扱おうとしている箇所があります:

```python
academics = search_arxiv(" ".join(tech_tags)) or ""
```

この場合、`search_arxiv`が空リストを返すと空文字列になりますが、結果がある場合は`List[Dict]`がそのまま渡されます。LLMへのプロンプトでは、このリストが文字列として扱われるため、適切にフォーマットする必要があります。

### 改善案

学術論文の結果を文字列形式に変換するヘルパー関数を追加:

```python
def format_arxiv_results(results: List[Dict]) -> str:
    """arXiv検索結果を文字列形式にフォーマット"""
    if not results:
        return "学術論文は見つかりませんでした。"
    
    formatted = []
    for paper in results:
        formatted.append(
            f"タイトル: {paper['title']}\n"
            f"著者: {', '.join(paper['authors'])}\n"
            f"公開日: {paper['published']}\n"
            f"リンク: {paper['link']}\n"
            f"要約: {paper['summary']}\n"
        )
    return "\n".join(formatted)
```

## 今後の改善案

1. **結果のフォーマット関数**: 検索結果を文字列形式に変換する関数を追加
2. **エラーハンドリングの改善**: より詳細なエラー処理とログ出力
3. **キャッシュ機能**: 同じクエリの再検索を避けるため、結果をキャッシュ
4. **検索クエリの最適化**: 日本語キーワードの英語変換や、より効果的なクエリ構築
5. **フィルタリング機能**: カテゴリや日付範囲でのフィルタリング
6. **並列検索**: 複数のキーワードで並列に検索して結果を統合

