# 🧪 R&D Brain - 研究開発アイデア創出AIエージェント

化学メーカーの研究開発アイデアを創出するAIエージェント「R&D Brain」のMVP（Minimum Viable Product）です。

営業担当者が面談録を入力すると、AIが内容を精査し、社内の他事業部の知見や市場トレンドを統合して、新規用途や改良アイデアを提案する戦略レポートを自動生成します。

## 📋 目次

- [主な機能](#主な機能)
- [技術スタック](#技術スタック)
- [セットアップ](#セットアップ)
- [使用方法](#使用方法)
- [プロジェクト構成](#プロジェクト構成)
- [環境変数の設定](#環境変数の設定)
- [Supabase設定](#supabase設定)
- [デプロイ](#デプロイ)

## 🚀 主な機能

### 1. 面談録の入力とAIレビュー
- 営業担当者が面談内容を入力
- GPT-4oが内容を自動評価
- 化学的な具体的なニーズ（温度、強度、耐性など）が含まれているかを判定
- 情報不足の場合は追加質問を提示

### 2. データベースへの保存
- 面談内容をEmbedding化してSupabaseに保存
- メタデータ（企業名、部署、事業部、技術タグ、登録日時）を付与

### 3. アイデア創出プロセス（自動実行）
データ登録完了後に自動で以下を実行：

#### 3.1 社内シーズの探索
- 他事業部の類似知見をベクトル検索で探索
- 現在の事業部と異なるデータのみを取得（クロスポリネーション）

#### 3.2 市場調査
- DuckDuckGo検索を使用して最新の市場トレンドを調査
- 技術タグと用途から関連する規制や新技術を検索

#### 3.3 戦略レポート生成
以下のセクションを含むMarkdownレポートを自動生成：
- **Trigger**: 今回の顧客の声（企業名・ニーズ）
- **Chemical Insight**: 抽出された化学的課題
- **Cross-Link**: 社内の他事業部にある類似知見（関連度とその理由）
- **Market Trend**: 関連する市場の動き
- **Proposal**: クラレとして提案すべき「新用途」または「改良アイデア」

## 🛠 技術スタック

- **フロントエンド**: Streamlit
- **バックエンド**: Python 3.12+
- **データベース**: Supabase (PostgreSQL + pgvector)
- **AI/ML**:
  - LangChain (LLM統合フレームワーク)
  - OpenAI GPT-4o (コンテンツレビュー・レポート生成)
  - OpenAI text-embedding-3-small (ベクトル化)
- **検索**: DuckDuckGo Search (市場調査)

## 📦 セットアップ

### 前提条件

- Python 3.12以上
- Supabaseアカウントとプロジェクト
- OpenAI APIキー

### インストール手順

1. **リポジトリのクローン**
```bash
git clone <repository-url>
cd product
```

2. **仮想環境の作成と有効化**
```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. **依存パッケージのインストール**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

4. **環境変数の設定**
プロジェクトルートに `.env` ファイルを作成し、以下の形式で設定：

```bash
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key
OPENAI_API_KEY=your-openai-api-key
```

`env.example` ファイルをコピーして `.env` ファイルを作成する方法：

```bash
cp env.example .env
# .envファイルを編集して実際の値を設定
```

詳細は [環境変数の設定](#環境変数の設定) を参照してください。

5. **Supabaseデータベースの設定**
`supabase_settings.txt` のSQLをSupabaseのSQL Editorで実行して、`match_documents` 関数を作成してください。

## 🎯 使用方法

### アプリケーションの起動

```bash
source venv/bin/activate  # 仮想環境が有効でない場合
streamlit run app.py
```

ブラウザで `http://localhost:8501` が自動的に開きます。

### 基本的な使い方

1. **事業部の選択**
   - サイドバーから事業部を選択（エバール事業部、イソプレン事業部、ジェネスタ事業部）

2. **面談情報の入力**
   - 企業名を入力
   - 相手方の部署・役職を入力
   - 面談メモを自由記述

3. **AIレビュー実行**
   - 「AIレビュー実行」ボタンをクリック
   - AIが内容を評価し、結果を表示

4. **データの登録**
   - 情報が十分な場合、「この内容で登録しますか？」ボタンをクリック
   - データがSupabaseに保存されます

5. **アイデア創出レポートの確認**
   - 登録完了後、自動的にアイデア創出プロセスが実行されます
   - 戦略レポートと他事業部の知見が表示されます

## 📁 プロジェクト構成

```
product/
├── app.py                 # Streamlitメインアプリケーション
├── backend.py             # Supabase接続・ベクトル検索機能
├── requirements.txt       # Python依存パッケージ
├── supabase_settings.txt # Supabase SQL設定
├── .gitignore           # Git除外設定
├── env.example          # 環境変数設定例
├── README.md            # このファイル
└── venv/                # 仮想環境（Git除外）
```

## 🔐 環境変数の設定

### 環境変数の設定方法

プロジェクトルートに `.env` ファイルを作成し、以下の形式で設定してください：

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
OPENAI_API_KEY=sk-...
```

`.env` ファイルは自動的に読み込まれます（`python-dotenv`を使用）。

### 環境変数の取得方法

#### Supabase
1. Supabaseプロジェクトのダッシュボードにアクセス
2. Settings > API から以下を取得：
   - **URL**: Project URL
   - **Key**: `anon` `public` キー

#### OpenAI
1. [OpenAI Platform](https://platform.openai.com/) にアクセス
2. API Keys から新しいキーを作成または既存のキーを取得

## 🗄️ Supabase設定

### データベーステーブル

`documents` テーブルが必要です。以下の構造で作成してください：

```sql
CREATE TABLE documents (
  id BIGSERIAL PRIMARY KEY,
  content TEXT NOT NULL,
  metadata JSONB,
  embedding vector(1536)
);
```

### 検索関数

`supabase_settings.txt` の内容をSupabaseのSQL Editorで実行してください。これにより、フィルタリング対応の `match_documents` 関数が作成されます。

## 🚢 デプロイ

### Streamlit Cloud

1. GitHubリポジトリにプッシュ
2. [Streamlit Cloud](https://streamlit.io/cloud) にログイン
3. "New app" をクリック
4. リポジトリとブランチを選択
5. Main file path: `app.py` を指定
6. Secrets に以下を設定：
   ```
   supabase_url = "your-supabase-url"
   supabase_key = "your-supabase-key"
   openai_api_key = "your-openai-api-key"
   ```
7. Deploy をクリック

### ローカル実行

```bash
streamlit run app.py
```

## 📝 注意事項

- OpenAI APIの使用には料金が発生します
- DuckDuckGo検索は無料ですが、レート制限があります
- Supabaseの無料プランには制限があります（データベースサイズ、APIリクエスト数など）
- 本アプリはMVPのため、本番環境での使用前に十分なテストを推奨します

## 🔄 今後の拡張予定

- [ ] ユーザー認証機能
- [ ] レポートのエクスポート機能（PDF、Excel）
- [ ] 過去のレポート一覧・検索機能
- [ ] 他事業部への通知機能
- [ ] より高度な市場分析機能

## 📄 ライセンス

このプロジェクトは社内利用を目的としています。

## 🤝 サポート

問題や質問がある場合は、プロジェクトの管理者に連絡してください。

---

**R&D Brain** - 化学メーカーの研究開発を加速するAIエージェント 🧪
