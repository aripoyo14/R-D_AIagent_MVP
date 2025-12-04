# 学術論文検索機能のテスト方法

## 概要

`test_academic_search.py`は、学術論文検索機能（`services/academic.py`）が正しく動作しているかを確認するためのテストスクリプトです。

## 前提条件

1. 仮想環境がアクティベートされていること
2. 必要なライブラリがインストールされていること（`requirements.txt`参照）

## 基本的な使用方法

### クイックテスト（推奨）

基本的な検索機能をテストします：

```bash
# 仮想環境をアクティベート
source venv/bin/activate

# デフォルトのクエリでテスト
python test_academic_search.py --quick

# カスタムクエリでテスト
python test_academic_search.py --quick --query "polymer heat resistance"

# 取得件数を指定
python test_academic_search.py --quick --query "機械学習" --max-results 10
```

### 全テスト実行

すべてのテストケースを実行します：

```bash
# デフォルトのクエリで全テスト実行
python test_academic_search.py

# カスタムクエリで全テスト実行
python test_academic_search.py --query "polymer" --max-results 5
```

## テスト内容

### テスト1: 基本的な検索
- arXiv APIを使用した検索機能の動作確認
- 検索結果の取得と表示
- 各論文のタイトル、著者、公開日、リンク、要約の確認

### テスト2: フォーマット関数
- `format_arxiv_results()`関数の動作確認
- 検索結果を文字列形式にフォーマットする機能の確認

### テスト3: 空の結果
- 検索結果が0件の場合の処理確認
- 適切なメッセージが返されることを確認

### テスト4: JSON出力
- 検索結果をJSON形式で出力する機能の確認
- データ構造の整合性確認

### テスト5: エラーハンドリング
- 無効なクエリ（空文字列など）に対するエラーハンドリングの確認
- 例外が適切に処理されることを確認

## 実行例

### 成功例

```bash
$ python test_academic_search.py --quick --query "machine learning" --max-results 3

クイックテスト: 'machine learning' で検索

================================================================================
テスト1: 基本的な検索
クエリ: 'machine learning'
最大取得件数: 3
================================================================================
✅ 3件の論文を取得しました。

【論文1】
  タイトル: Changing Data Sources in the Age of Machine Learning for Official Statistics
  著者: Cedric De Boom, Michael Reusens
  公開日: 2023-06-07
  リンク: http://arxiv.org/abs/2306.04338v1
  要約（最初の200文字）: Data science has become increasingly essential...
```

### ログ出力

テスト実行時には、以下のようなログが出力されます：

```
2025-12-04 17:29:16,268 - services.academic - INFO - arXiv検索開始: query='machine learning', max_results=3
2025-12-04 17:29:18,256 - services.academic - INFO - arXiv検索完了: 3件の論文を取得
```

## トラブルシューティング

### ModuleNotFoundError: No module named 'arxiv'

**原因**: 仮想環境がアクティベートされていない、またはライブラリがインストールされていない

**解決方法**:
```bash
# 仮想環境をアクティベート
source venv/bin/activate

# ライブラリをインストール
pip install -r requirements.txt
```

### 検索結果が0件

**原因**: 
- クエリがarXivに存在しない
- ネットワーク接続の問題
- arXiv APIの一時的な問題

**解決方法**:
- 別のクエリで試す
- ネットワーク接続を確認
- しばらく時間をおいて再試行

### タイムアウトエラー

**原因**: ネットワークが遅い、またはarXiv APIが応答しない

**解決方法**:
- ネットワーク接続を確認
- しばらく時間をおいて再試行
- `max_results`を減らして再試行

## コマンドライン引数

| 引数 | 説明 | デフォルト値 |
|------|------|-------------|
| `--query` | 検索クエリ文字列 | `"polymer"` |
| `--max-results` | 最大取得件数 | `5` |
| `--quick` | クイックテストモード（基本的な検索のみ） | `False` |

## テスト結果の解釈

- ✅ **PASS**: テストが成功したことを示します
- ❌ **FAIL**: テストが失敗したことを示します

全テストが成功すると、スクリプトは終了コード0で終了します。いずれかのテストが失敗すると、終了コード1で終了します。

## 統合テストでの使用

CI/CDパイプラインで使用する場合：

```bash
# テストが成功するか確認
python test_academic_search.py --quick --query "test" && echo "Tests passed" || exit 1
```

## 関連ファイル

- `services/academic.py`: 学術論文検索の実装
- `services/multi_agent.py`: マルチエージェントシステムでの使用箇所
- `docs/academic_search.md`: 実装の詳細ドキュメント

