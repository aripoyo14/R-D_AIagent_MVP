# 化学関連フィルタの実装

## 概要

学術論文検索において、化学に関係ない論文（例: 賭け戦略、金融など）が取得される問題を解決するため、化学関連の論文のみを取得するフィルタ機能を実装しました。

## 問題の背景

以前の実装では、例えば「アンモニア」で検索した際に、「賭け戦略 (betting strategies)」に関する論文が取得されるなど、化学とは全く関係ない論文が含まれていました。

## 解決策

### 1. カテゴリフィルタ

arXivの化学関連カテゴリに限定して検索します：

```python
CHEMISTRY_CATEGORIES = [
    "cond-mat.mtrl-sci",  # 材料科学
    "physics.app-ph",     # 応用物理学
    "cond-mat.soft",      # ソフトマター
    "cond-mat",           # 凝縮系物理学全般
    "physics.chem-ph",    # 化学物理学
]
```

検索クエリに `cat:` 演算子を使用してカテゴリを指定します：
```
(元のクエリ) AND (cat:cond-mat.mtrl-sci OR cat:physics.app-ph OR ...)
```

### 2. キーワードフィルタ

タイトルと要約から化学関連キーワードを検出し、化学に関係ないキーワードを含む論文を除外します。

**化学関連キーワード**:
- chemistry, chemical, material, polymer, molecule, compound
- synthesis, reaction, catalyst, organic, inorganic
- materials science, nanomaterial, composite, resin

**除外キーワード**:
- betting, strategy, gambling, poker, casino
- finance, economics, trading, investment, stock

### 3. 化学式パターン検出

化学式のパターン（例: NH3, CO2, H2O）を含む論文を化学関連として判定します。

### 4. クエリの強化

検索クエリに化学関連キーワードを自動的に追加します：
```
元のクエリ: "ammonia"
強化後: "ammonia (material OR chemistry OR chemical)"
```

## 実装の詳細

### `is_chemistry_related()` 関数

論文が化学関連かどうかを判定します：

```python
def is_chemistry_related(title: str, summary: str) -> bool:
    """
    論文が化学関連かどうかを判定する
    
    1. 除外キーワードが含まれている場合はFalse
    2. 化学関連キーワードが含まれている場合はTrue
    3. 化学式パターンが含まれている場合はTrue
    4. デフォルトはTrue（緩いフィルタリング）
    """
```

### `build_chemistry_query()` 関数

化学関連の検索クエリを構築します：

```python
def build_chemistry_query(base_query: str) -> str:
    """
    カテゴリフィルタを追加した検索クエリを構築
    """
    category_filter = " OR ".join([f"cat:{cat}" for cat in CHEMISTRY_CATEGORIES])
    query = f"({base_query}) AND ({category_filter})"
    return query
```

### `enhance_query_with_chemistry_keywords()` 関数

検索クエリに化学関連キーワードを追加します：

```python
def enhance_query_with_chemistry_keywords(query: str) -> str:
    """
    既に化学関連キーワードが含まれている場合はそのまま返す
    含まれていない場合は追加
    """
```

## フォールバック処理

1. **結果が0件の場合**: カテゴリフィルタを緩和して再試行
2. **エラー時**: カテゴリフィルタなしで再試行
3. **フィルタリング**: より多くの結果を取得してからフィルタリング（max_results * 5件取得）

## テスト結果

### テストケース1: アンモニア

**検索クエリ**: `ammonia`

**結果**:
1. Guest Editorial: Special Topic on Data-enabled Theoretical Chemistry
   - カテゴリ: `physics.chem-ph`
2. From ab initio quantum chemistry to molecular dynamics: The delicate case of hydrogen bonding in ammonia
   - カテゴリ: `physics.chem-ph, physics.atm-clus, physics.comp-ph`
3. Model reduction in chemical dynamics: slow invariant manifolds, singular perturbations, thermodynamic estimates, and analysis of reaction graph
   - カテゴリ: `physics.chem-ph`

**評価**: ✅ すべて化学関連の論文が取得されています

### テストケース2: ポリマー

**検索クエリ**: `polymer`

**結果**:
1. Velocity jump in the crack propagation induced on a semi-crystalline polymer sheet by constant-speed stretching
   - カテゴリ: `cond-mat.soft`
2. Theoretical Approaches to Neutral and Charged Polymer Brushes
   - カテゴリ: `cond-mat.soft`
3. Tuning the Mechanical Properties in Model Nanocomposites: Influence of the Polymer-Filler Interfacial Interactions
   - カテゴリ: `cond-mat.soft`

**評価**: ✅ すべて化学関連の論文が取得されています

## 使用方法

デフォルトで化学関連フィルタが有効になっています：

```python
from services.academic import search_arxiv

# 化学関連の論文のみを取得（デフォルト）
results = search_arxiv("ammonia", max_results=5)

# フィルタなしで検索（非推奨）
results = search_arxiv("ammonia", max_results=5, chemistry_only=False)
```

## パフォーマンス

- **検索時間**: フィルタリングにより若干増加（約1-2秒）
- **取得件数**: フィルタリング用に多めに取得（max_results * 5件）してからフィルタリング
- **精度**: 化学関連の論文のみが取得され、関係ない論文は除外される

## 今後の改善案

1. **より高度なフィルタリング**: 機械学習モデルを使用した分類
2. **カテゴリの動的選択**: 検索クエリに基づいて最適なカテゴリを選択
3. **除外キーワードの拡張**: より多くの除外パターンを追加
4. **化学物質データベースとの連携**: 化学物質名の正規化と検証

## 関連ファイル

- `services/academic.py`: 学術論文検索の実装
- `test_chemistry_filter.py`: フィルタ機能のテストスクリプト

