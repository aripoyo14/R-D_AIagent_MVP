# 検索クエリの構築方法

## 概要

本システムでは、複数の情報源から市場情報を取得するために、それぞれ異なる方法で検索クエリを構築しています。このドキュメントでは、各検索機能でのクエリ構築方法を詳しく説明します。

## 検索クエリの生成フロー

```
面談メモ入力
    ↓
AIレビュー（services/ai_review.py）
    ↓
tech_tags抽出（LLM: Gemini 2.5 Pro）
    ↓
重要度の高いタグを選定（最大5つ）
    ↓
各検索機能でクエリ構築
    ├─ 学術論文検索（arXiv）
    ├─ 特許検索（Google Patents）
    ├─ 市場トレンド検索（DuckDuckGo）
    └─ ニュース検索（DuckDuckGo）
```

## 1. 技術タグ（tech_tags）の抽出

### 抽出元

**ファイル**: `services/ai_review.py`

**関数**: `review_interview_content(content: str) -> ReviewResult`

**プロセス**:
1. 面談メモの内容をLLM（Gemini 2.5 Pro）に送信
2. LLMが面談メモから技術タグを抽出
3. `ReviewResult.tech_tags`として返却

**抽出される内容**:
- 材料名（例: "polymer", "ポリマー"）
- 用途（例: "automotive", "自動車部品"）
- 特性（例: "heat resistance", "耐熱性"）
- 技術領域（例: "material science", "材料科学"）

**プロンプト**:
```25:41:services/ai_review.py
REVIEW_PROMPT_TEMPLATE = """あなたは化学メーカーの研究開発部門の専門家です。出力は必ず日本語で記載してください。
面談メモの内容を評価し、以下の基準で判断してください：

【評価基準】
- 化学的な「具体的なニーズ」が含まれているか？
  - 温度条件（例: 100℃以上、-20℃以下）
  - 強度・物性（例: 引張強度100MPa以上、弾性率）
  - 耐性（例: 耐熱性、耐薬品性、耐候性）
  - その他の具体的な数値や仕様

【出力形式】
- 情報が十分な場合: is_sufficient=true, summary（要約）とtech_tags（技術タグのリスト）を提供
- 情報が不足している場合: is_sufficient=false, questions（追加で聞くべき質問のリスト）を提供

技術タグは、材料名、用途、特性、技術領域などを含めてください。

{format_instructions}"""
```

**例**:
```python
# 入力: "顧客から高温環境下でも劣化しないポリマー材料の開発依頼がありました。"
# 出力: tech_tags = ["polymer", "heat resistance", "automotive", "耐熱性"]
```

### 重要度の高いタグの選定

**ファイル**: `services/ai_review.py`

**関数**: `select_important_tags(tech_tags: List[str], interview_memo: str = "", max_tags: int = 5) -> List[str]`

**プロセス**:
1. 技術タグが5つ以下の場合はそのまま返す
2. 5つを超える場合は、LLM（Gemini 2.5 Flash）を使用して重要度の高いタグを選定
3. 選定基準:
   - 材料名や化学物質名を優先
   - 用途や応用分野を優先
   - 具体的な物性や特性を優先
   - 技術領域やプロセス名を優先
   - 一般的すぎるキーワードは除外

**選定例**:
```python
# 入力: 19個の技術タグ
tech_tags = [
    "EUVレジスト", "メタル酸化物レジスト", "MOR", "2nmプロセスノード",
    "半導体リソグラフィ", "高解像度", "高感度", "低LWR", ...
]

# 出力: 重要度の高い5つのタグ
selected_tags = [
    "EUVレジスト", "メタル酸化物レジスト", "有機ハイブリッド材料",
    "2nmプロセスノード", "高解像度"
]
```

**特徴**:
- 化学系製造業にとって重要度の高いタグを選定
- クエリの長さを最適化し、検索精度を向上
- エラー時は最初の5つのタグを返す（フォールバック）

## 2. 各検索機能でのクエリ構築

### 2.1 学術論文検索（arXiv）

**ファイル**: `services/multi_agent.py` → `services/academic.py`

**呼び出し箇所**:
```python
# services/multi_agent.pyのagent_market_researcher関数内
selected_tags = select_important_tags(tech_tags, interview_memo=use_case, max_tags=5)
academics_list = search_arxiv(" ".join(selected_tags))
```

**クエリ構築方法**:
- **方法**: `tech_tags`をスペース区切りで結合
- **形式**: `" ".join(tech_tags)`
- **例**: `tech_tags = ["polymer", "heat resistance"]` → `"polymer heat resistance"`

**実装コード**:
```11:33:services/academic.py
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
```

**特徴**:
- シンプルなキーワード結合
- arXiv APIが自動的にAND検索として解釈
- 関連度順でソート

**例**:
```
入力: tech_tags = ["polymer", "heat resistance"]
クエリ: "polymer heat resistance"
```

### 2.2 特許検索（Google Patents）

**ファイル**: `services/patents.py`

**呼び出し箇所**:
```python
# services/multi_agent.pyのagent_market_researcher関数内
selected_tags = select_important_tags(tech_tags, interview_memo=use_case, max_tags=5)
patents = search_patents(selected_tags) or ""
```

**クエリ構築方法**:
- **方法**: `tech_tags`をスペース区切りで結合 + `site:patents.google.com` + 年号
- **形式**: `f"site:patents.google.com {query_str} 2024 2025"`
- **例**: `tech_tags = ["polymer", "heat resistance"]` → `"site:patents.google.com polymer heat resistance 2024 2025"`

**実装コード**:
```18:22:services/patents.py
        # Google Patentsを対象としたクエリの構築
        # 例: "site:patents.google.com polymer heat resistance 2024"
        query_str = " ".join(keywords)
        query = f"site:patents.google.com {query_str} 2024 2025"
```

**特徴**:
- `site:`演算子でGoogle Patentsに限定
- 年号（2024 2025）を追加して最新の特許を優先
- DuckDuckGo検索エンジン経由で検索

**例**:
```
入力: tech_tags = ["polymer", "heat resistance"]
クエリ: "site:patents.google.com polymer heat resistance 2024 2025"
```

### 2.3 市場トレンド検索（DuckDuckGo）

**ファイル**: `backend.py`

**呼び出し箇所**:
```python
# services/multi_agent.pyのagent_market_researcher関数内
selected_tags = select_important_tags(tech_tags, interview_memo=use_case, max_tags=5)
results = backend.search_market_trends(selected_tags, use_case) or ""
```

**クエリ構築方法**:
- **方法**: `tech_tags`をカンマ区切りで結合 + 用途説明（最大180文字） + 固定キーワード
- **形式**: `f"{tags_str} {use_case_trimmed} 市場トレンド 規制 新技術 2024 2025"`
- **最大長**: 512文字に制限
- **例**: 
  - `tech_tags = ["polymer", "heat resistance"]`
  - `use_case = "自動車部品への応用"`
  - → `"polymer, heat resistance 自動車部品への応用 市場トレンド 規制 新技術 2024 2025"`

**実装コード**:
```186:191:backend.py
        # 検索クエリを生成（面談メモをそのまま入れるとURLが長くなるため整形＋上限）
        tags_str = ", ".join(tech_tags)
        use_case_trimmed = " ".join(use_case.split())[:180] if use_case else ""
        query_parts = [tags_str, use_case_trimmed, "市場トレンド 規制 新技術 2024 2025"]
        query = " ".join([p for p in query_parts if p]).strip()[:512]
```

**特徴**:
- カンマ区切りで技術タグを結合（検索エンジンでのAND検索を促進）
- 用途説明（`use_case`）を含めることで文脈を追加
- 固定キーワード（"市場トレンド 規制 新技術 2024 2025"）で最新の市場情報を優先
- URL長制限を考慮して512文字に制限

**例**:
```
入力: 
  tech_tags = ["polymer", "heat resistance"]
  use_case = "顧客から高温環境下でも劣化しないポリマー材料の開発依頼がありました。現在使用している材料は120度以上の温度で強度が低下する問題があります。自動車部品への応用を想定しており、耐熱性とコストのバランスが重要です。"

クエリ: "polymer, heat resistance 顧客から高温環境下でも劣化しないポリマー材料の開発依頼がありました。現在使用している材料は120度以上の温度で強度が低下する問題があります。自動車部品への応用を想定しており、耐熱性とコストのバランスが重要です。 市場トレンド 規制 新技術 2024 2025"
（実際には180文字に切り詰められる）
```

### 2.4 ニュース検索（DuckDuckGo）

**ファイル**: `services/news.py`

**注意**: 現在、`agent_market_researcher`では使用されていませんが、将来的に使用される可能性があります。

**クエリ構築方法**:
- **方法**: `tech_tags`をスペース区切りで結合 + 固定キーワード + 企業名（オプション）
- **形式**: 
  - 企業名あり: `f"{company_name} {tags_str} (news OR ニュース OR プレスリリース OR 新製品) 2024 2025"`
  - 企業名なし: `f"化学業界 {tags_str} (news OR ニュース OR プレスリリース OR 新製品) 2024 2025"`

**実装コード**:
```19:28:services/news.py
        # クエリの構築
        # 例: "ポリマー 耐熱性 (news OR ニュース OR プレスリリース OR 新製品) 2024 2025"
        tags_str = " ".join(keywords)
        
        base_query = f"{tags_str} (news OR ニュース OR プレスリリース OR 新製品) 2024 2025"
        
        if company_name:
            query = f"{company_name} {base_query}"
        else:
            query = f"化学業界 {base_query}"
```

**特徴**:
- OR演算子で複数のニュース関連キーワードを検索
- 企業名がある場合は企業名を先頭に追加
- 企業名がない場合は"化学業界"を追加して業界ニュースに限定

**例**:
```
入力: 
  keywords = ["polymer", "heat resistance"]
  company_name = ""

クエリ: "化学業界 polymer heat resistance (news OR ニュース OR プレスリリース OR 新製品) 2024 2025"
```

## 3. クエリ構築の比較表

| 検索機能 | 区切り文字 | 追加キーワード | 年号 | その他 |
|---------|-----------|--------------|------|--------|
| 学術論文検索 | スペース (`" "`) | なし | なし | 関連度順ソート |
| 特許検索 | スペース (`" "`) | `site:patents.google.com` | `2024 2025` | Google Patents限定 |
| 市場トレンド検索 | カンマ+スペース (`", "`) | `市場トレンド 規制 新技術` | `2024 2025` | 用途説明を含む、最大512文字 |
| ニュース検索 | スペース (`" "`) | `(news OR ニュース OR プレスリリース OR 新製品)` | `2024 2025` | 企業名または"化学業界"を追加 |

## 4. クエリ構築の設計思想

### 4.1 学術論文検索

- **シンプルさ重視**: arXiv APIが高度な検索構文をサポートしているため、シンプルなキーワード結合で十分
- **関連度順**: 検索エンジンの関連度アルゴリズムに任せる

### 4.2 特許検索

- **サイト限定**: `site:`演算子でGoogle Patentsに限定し、ノイズを削減
- **年号追加**: 最新の特許を優先的に取得

### 4.3 市場トレンド検索

- **文脈の追加**: 用途説明を含めることで、より関連性の高い結果を取得
- **固定キーワード**: "市場トレンド 規制 新技術"で検索範囲を明確化
- **長さ制限**: URL長制限を考慮して512文字に制限

### 4.4 ニュース検索

- **複数言語対応**: 日本語と英語のニュース関連キーワードをOR検索
- **業界限定**: 企業名がない場合は"化学業界"を追加

## 5. クエリの最適化のヒント

### 5.1 技術タグの品質向上

- **具体的なキーワード**: より具体的な技術タグを抽出することで、検索精度が向上
- **英語キーワード**: 学術論文や特許は英語が多いため、英語のキーワードが効果的
- **複数表現**: 同じ概念の異なる表現を含める（例: "polymer"と"ポリマー"）

### 5.2 用途説明の活用

- **市場トレンド検索**: 用途説明を含めることで、より関連性の高い結果を取得
- **長さの調整**: 用途説明が長すぎる場合は、重要な部分のみを抽出

### 5.3 年号の更新

- **固定年号**: 現在は"2024 2025"がハードコードされている
- **改善案**: 動的に現在の年を取得して更新する

## 6. 今後の改善案

1. **動的年号**: 現在の年を自動的に取得してクエリに追加
2. **クエリの最適化**: LLMを使用してクエリを最適化
3. **多言語対応**: 日本語と英語のキーワードを適切に組み合わせ
4. **検索結果のフィードバック**: 検索結果の品質に基づいてクエリを調整
5. **クエリのキャッシュ**: 同じクエリの再検索を避けるため、結果をキャッシュ

## 7. 関連ファイル

- `services/ai_review.py`: 技術タグの抽出
- `services/multi_agent.py`: 各検索機能の呼び出し
- `services/academic.py`: 学術論文検索
- `services/patents.py`: 特許検索
- `backend.py`: 市場トレンド検索
- `services/news.py`: ニュース検索

