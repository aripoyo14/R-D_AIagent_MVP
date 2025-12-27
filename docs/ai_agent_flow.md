# AI Agentの働きと技術解説：面談録登録からレポート表示まで

## 📋 目次

1. [全体フロー概要](#全体フロー概要)
2. [ステップ1：面談録入力](#ステップ1面談録入力)
3. [ステップ2：AIレビュー](#ステップ2aiレビュー)
4. [ステップ3：データベース保存](#ステップ3データベース保存)
5. [ステップ4：イノベーション分隊の議論](#ステップ4イノベーション分隊の議論)
6. [ステップ5：レポート表示](#ステップ5レポート表示)
7. [使用技術とライブラリ一覧](#使用技術とライブラリ一覧)

---

## 全体フロー概要

```
┌─────────────────────────────────────────────────────────────┐
│  ステップ1: 面談録入力                                        │
│  - ユーザーが企業名、部署・役職、面談メモを入力              │
│  - ファイルアップロード（docx/txt/pdf）対応                  │
│  📁 実装: app.py, components/sidebar.py                      │
└─────────────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│  ステップ2: AIレビュー                                        │
│  - Gemini APIが内容の十分性を判定                            │
│  - 技術タグを自動抽出                                         │
│  - 情報不足の場合は追加質問を提示                            │
│  📁 実装: services/ai_review.py                              │
│  🤖 AI: Google Gemini 2.5 Flash/Pro                         │
│  📚 ライブラリ: LangChain, Pydantic                          │
└─────────────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│  ステップ3: データベース保存                                  │
│  - 面談内容をベクトル化（Embedding）                         │
│  - メタデータと共にSupabaseに保存                            │
│  📁 実装: backend.py                                         │
│  🤖 AI: OpenAI Embeddings (text-embedding-3-small)          │
│  🗄️ データベース: Supabase (PostgreSQL + pgvector)          │
└─────────────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│  ステップ4: イノベーション分隊の議論（5人のAIエージェント）   │
│                                                              │
│  4.1 👑 オーケストレーター                                    │
│     - チームへのブリーフィング作成                            │
│     - 議論の進行管理                                          │
│     - 最終レポートの統合                                      │
│                                                              │
│  4.2 🕵️ マーケットリサーチャー                                │
│     - DuckDuckGo検索で市場トレンド調査                        │
│     - Google Patentsで特許情報検索                            │
│     - arXivで学術論文検索                                     │
│                                                              │
│  4.3 🔍 インターナルスペシャリスト                            │
│     - 他事業部の類似知見をベクトル検索                        │
│     - クロスポリネーションの実現                              │
│                                                              │
│  4.4 💡 ソリューションアーキテクト                            │
│     - 市場データと社内データを統合                            │
│     - 初期提案を作成                                          │
│     - フィードバックを踏まえた改善案を作成                    │
│                                                              │
│  4.5 👿 デビルズアドボケイト                                  │
│     - 提案のリスクと課題を厳しく指摘                          │
│     - 化学リスク、コスト、量産問題を検証                      │
│                                                              │
│  📁 実装: services/multi_agent.py, services/patents.py,     │
│          services/academic.py                               │
│  🤖 AI: Google Gemini 2.5 Flash/Pro                         │
│  📚 ライブラリ: LangChain, DuckDuckGo Search, arXiv         │
└─────────────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│  ステップ5: レポート表示                                      │
│  - Markdown形式の戦略レポート                                │
│  - 他事業部の類似知見（関連度付き）                          │
│  - 学術論文情報                                              │
│  - LINE風UIでの会話ログ表示                                 │
│  - スライド形式でのエクスポート                              │
│  📁 実装: components/idea_report.py, components/            │
│          conversation_log.py, services/slide_report2.py     │
└─────────────────────────────────────────────────────────────┘
```

---

## ステップ1：面談録入力

### 概要
ユーザー（営業担当者）が顧客との面談内容を入力します。

### 実装ファイル
- `app.py`: Streamlitのメインアプリケーション
- `components/sidebar.py`: サイドバーの入力フォーム

### 入力項目
1. **事業部選択**：現在の事業部を選択
2. **企業名**：顧客企業名
3. **相手方 部署・役職**：顧客の担当者情報
4. **面談メモ**：
   - テキスト入力
   - ファイルアップロード（docx/txt/pdf対応）

### 使用ライブラリ
```python
import streamlit as st           # UIフレームワーク
from python-docx import Document # Word文書の読み込み
import pypdf                     # PDF文書の読み込み
```

### コード例

```python
# app.py から抜粋
def main():
    st.set_page_config(
        page_title="Alchemy 5",
        page_icon="🤖",
        layout="wide"
    )
    
    # サイドバーで入力フォームを表示
    with st.sidebar:
        selected_department, api_keys_ok, form_data, model_name = render_sidebar(review_container)
```

### 特徴
- **ファイルアップロード対応**：Word、テキスト、PDFファイルを自動解析
- **事業部選択**：選択した事業部以外の知見を検索対象とする（クロスポリネーション）
- **入力検証**：必須項目のチェックをフロントエンドで実施

---

## ステップ2：AIレビュー

### 概要
Google Gemini APIを使用して、面談内容の十分性を自動判定し、技術タグを抽出します。

### 実装ファイル
- `services/ai_review.py`: AIレビューサービス

### 処理フロー
1. **面談内容の解析**
2. **情報の十分性判定**
   - 化学的な具体的なニーズが含まれているか
   - 温度条件、強度・物性、耐性などの具体的な数値
3. **技術タグの抽出**
   - 材料名、用途、特性、技術領域などを抽出
4. **結果の返却**
   - 情報が十分な場合：要約と技術タグを返す
   - 情報が不足している場合：追加質問を返す

### 使用AI・ライブラリ

#### AI モデル
```python
# Google Gemini 2.5 Flash/Pro を使用
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",  # または "gemini-2.5-pro"
    temperature=0.3,
    google_api_key=os.getenv("GEMINI_API_KEY")
)
```

#### ライブラリ
```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
```

### コード例

```python
# services/ai_review.py から抜粋
class ReviewResult(BaseModel):
    """AIレビューの結果を格納するモデル"""
    is_sufficient: bool = Field(description="情報が十分かどうか")
    questions: List[str] = Field(default=[], description="情報不足の場合の質問リスト")
    summary: Optional[str] = Field(default=None, description="内容の要約")
    tech_tags: List[str] = Field(default=[], description="抽出された技術タグ")


def review_interview_content(content: str, model_name: str = "gemini-2.5-flash-lite") -> ReviewResult:
    """Gemini 2.5 を使用して面談内容をレビューする"""
    
    # LLMを初期化
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        temperature=0.3,
        google_api_key=os.getenv("GEMINI_API_KEY")
    )
    
    # 出力パーサーを設定（Pydanticモデルで構造化）
    parser = PydanticOutputParser(pydantic_object=ReviewResult)
    
    # プロンプトテンプレート
    prompt = ChatPromptTemplate.from_messages([
        ("system", REVIEW_PROMPT_TEMPLATE),
        ("human", "以下の面談メモを評価してください：\n\n{content}")
    ])
    
    # LLMを呼び出し
    response = llm.invoke(formatted_prompt)
    
    # 結果をパース
    result = parser.parse(response.content)
    return result
```

### 技術的なポイント

1. **構造化出力（Pydantic）**
   - `PydanticOutputParser`を使用して、AIの出力を構造化
   - `ReviewResult`モデルで、必要なフィールドを定義
   - JSONスキーマを自動生成し、LLMに指示

2. **プロンプトエンジニアリング**
   - 評価基準を明確に定義（温度条件、強度・物性、耐性など）
   - 出力形式を指定（`is_sufficient`, `summary`, `tech_tags`）
   - 日本語での出力を指示

3. **デフォルトタグの設定**
   - 技術タグが取得できない場合のフォールバック処理
   - `DEFAULT_TECH_TAGS`に化学関連のデフォルトタグを定義

---

## ステップ3：データベース保存

### 概要
面談内容をベクトル化（Embedding）し、Supabaseに保存します。これにより、後で他事業部の類似知見を検索できるようになります。

### 実装ファイル
- `backend.py`: バックエンドモジュール

### 処理フロー
1. **テキストのベクトル化**
   - OpenAI Embeddings API（text-embedding-3-small）を使用
   - 1536次元のベクトルに変換
2. **メタデータの付与**
   - 企業名、部署・役職、事業部、技術タグ、登録日時
3. **Supabaseへの保存**
   - PostgreSQL + pgvector拡張を使用
   - ベクトル検索に対応

### 使用AI・ライブラリ

#### AI モデル
```python
# OpenAI Embeddings API を使用
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=os.getenv("OPENAI_API_KEY")
)
```

#### データベース
```python
from supabase import create_client, Client
from langchain_community.vectorstores import SupabaseVectorStore
```

### コード例

```python
# backend.py から抜粋
def save_interview_note(text: str, metadata: Dict) -> bool:
    """
    面談内容をEmbedding化してSupabaseに保存する
    
    Args:
        text: 面談内容のテキスト
        metadata: メタデータ（企業名、役職、事業部、技術タグ、登録日時など）
    
    Returns:
        bool: 保存成功時True
    """
    # Embeddingモデルを初期化
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # テキストをEmbedding化
    embedding = embeddings.embed_query(text)
    
    # メタデータに登録日時を追加
    if "created_at" not in metadata:
        from datetime import datetime
        metadata["created_at"] = datetime.now().isoformat()
    
    # Supabaseクライアントを取得
    supabase = get_supabase_client()
    
    # Supabaseに挿入
    response = supabase.table("documents").insert({
        "content": text,
        "metadata": metadata,
        "embedding": embedding
    }).execute()
    
    return True
```

### データベーススキーマ

```sql
-- Supabase (PostgreSQL + pgvector)
CREATE TABLE documents (
  id BIGSERIAL PRIMARY KEY,
  content TEXT NOT NULL,
  metadata JSONB,
  embedding vector(1536)
);

-- ベクトル検索用のインデックス
CREATE INDEX documents_embedding_idx ON documents 
USING ivfflat (embedding vector_cosine_ops);

-- メタデータ検索用のインデックス
CREATE INDEX documents_metadata_idx ON documents USING GIN (metadata);
```

### 技術的なポイント

1. **ベクトル化（Embedding）**
   - OpenAI Embeddings API（text-embedding-3-small）を使用
   - テキストを1536次元のベクトルに変換
   - 意味的な類似性を数値化

2. **pgvector拡張**
   - PostgreSQLでベクトル検索を実現
   - コサイン類似度で類似文書を検索
   - IVFFlat（Inverted File Flat）インデックスで高速検索

3. **メタデータ管理**
   - JSONB型でメタデータを柔軟に保存
   - 企業名、事業部、技術タグなどのフィルタリングに使用

---

## ステップ4：イノベーション分隊の議論

### 概要
5人のAIエージェントが協力して、顧客のニーズに対する提案を作成します。各エージェントは異なる役割を持ち、それぞれの専門性を活かして議論を進めます。

### 実装ファイル
- `services/multi_agent.py`: イノベーション分隊の中核ロジック
- `services/patents.py`: 特許検索サービス
- `services/academic.py`: 学術論文検索サービス
- `services/report_generator.py`: レポート生成サービス

### 処理フロー

```
1. オーケストレーター: ブリーフィング作成
         ↓
2. マーケットリサーチャー: 市場調査（DuckDuckGo、特許、学術論文）
3. インターナルスペシャリスト: 社内知見検索（ベクトル検索）
         ↓
4. オーケストレーター: 議論の方向性を指示
         ↓
5. ソリューションアーキテクト: 初期提案を作成
         ↓
6. オーケストレーター: 批判的レビューを指示
         ↓
7. デビルズアドボケイト: リスク分析と批判
         ↓
8. オーケストレーター: 改善指示を出す
         ↓
9. ソリューションアーキテクト: 最終提案を作成
         ↓
10. オーケストレーター: 最終レポートを統合
```

---

### 4.1 👑 オーケストレーター（PM）

#### 役割
- チームへのブリーフィング作成
- 議論の進行管理
- 最終レポートの統合

#### 実装コード

```python
# services/multi_agent.py から抜粋
def generate_orchestrator_brief(interview_memo: str, model_name: str = "gemini-2.5-flash-lite") -> str:
    """👑司会用の短いブリーフを生成する。"""
    
    llm = get_llm(temperature=0.5, model_name=model_name)
    prompt = (
        "あなたはオーケストレーターです。以下の面談メモを読み、1段落で司会用ブリーフを作成してください。"
        "回答は必ず日本語で記載してください。"
        "含める要素: 主課題/要求スペック、競合・材料の候補、主要リスク、納期があれば明示、各エージェントへの指示"
        " (Market=事実調査, Internal=社内知見, Architect=発想, Devil=リスク確認)。"
        f"\n\n面談メモ:\n{interview_memo}"
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content.strip()
```

#### 使用AI
- Google Gemini 2.5 Flash/Pro
- LangChain の `ChatGoogleGenerativeAI`

---

### 4.2 🕵️ マーケットリサーチャー（外の目）

#### 役割
- 市場トレンドの調査（DuckDuckGo検索）
- 特許情報の検索（Google Patents）
- 学術論文の検索（arXiv）
- 競合他社、市場規模、トレンドをまとめる

#### 実装コード

```python
# services/multi_agent.py から抜粋
def agent_market_researcher(tech_tags: List[str], use_case: str = "", model_name: str = "gemini-2.5-flash-lite") -> tuple[str, List[Dict]]:
    """🕵️市場調査エージェント。DuckDuckGo で市場トレンドを検索。"""
    
    # 重要度の高いタグを選定（最大5つ）
    selected_tags = select_important_tags(tech_tags, interview_memo=use_case, max_tags=5, model_name=model_name)
    
    # 市場トレンド検索
    results = backend.search_market_trends(selected_tags, use_case) or ""
    
    # 特許検索
    patents = search_patents(selected_tags) or ""
    
    # 学術論文検索
    academics_list = search_arxiv(" ".join(selected_tags))
    academics = format_arxiv_results(academics_list) if academics_list else ""
    
    # LLMで要約
    llm = get_llm(temperature=0.3, model_name=model_name)
    response = llm.invoke([HumanMessage(content=prompt)])
    summary = response.content.strip()
    
    return summary, academics_list
```

#### 使用API・ライブラリ

1. **市場トレンド検索（DuckDuckGo）**
```python
# backend.py から抜粋
from ddgs import DDGS

def search_market_trends(tech_tags: List[str], use_case: str = "") -> str:
    """技術タグと用途を元に、最新の市場トレンドを検索する"""
    
    # 検索クエリを生成
    query = " ".join(tech_tags + ["市場トレンド 規制 新技術 2024 2025"])
    
    # DuckDuckGo検索を実行
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=5))
    
    return "\n".join(f"{r['title']} - {r['body']}" for r in results)
```

2. **特許検索（Google Patents）**
```python
# services/patents.py から抜粋
from ddgs import DDGS

def search_patents(keywords: List[str], max_results: int = 5) -> str:
    """DuckDuckGoを使用してGoogle Patentsから特許を検索"""
    
    # Google Patentsを対象としたクエリの構築
    query_str = " ".join(keywords)
    query = f"site:patents.google.com {query_str} 2024 2025"
    
    results_list = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results_list.append(f"Title: {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}\n")
    
    return "\n".join(results_list)
```

3. **学術論文検索（arXiv）**
```python
# services/academic.py から抜粋
import arxiv

def search_arxiv(query: str, max_results: int = 5, chemistry_only: bool = True) -> List[Dict]:
    """arXivで学術論文を検索します。"""
    
    # クライアントの構築
    client = arxiv.Client()
    
    # 化学関連のクエリを構築
    if chemistry_only:
        enhanced_query = enhance_query_with_chemistry_keywords(query)
        search_query = build_chemistry_query(enhanced_query)
    
    # 検索オブジェクトの構築
    search = arxiv.Search(
        query=search_query,
        max_results=max_results * 5,  # フィルタリング用に多めに取得
        sort_by=arxiv.SortCriterion.Relevance
    )
    
    results = []
    for result in client.results(search):
        # 化学関連のフィルタリング
        if chemistry_only and not is_chemistry_related(result.title, result.summary):
            continue
        
        results.append({
            "title": result.title,
            "summary": result.summary.replace("\n", " "),
            "authors": [author.name for author in result.authors],
            "link": result.entry_id,
            "published": result.published.strftime("%Y-%m-%d"),
            "categories": result.categories
        })
    
    return results
```

#### 使用ライブラリ
- `duckduckgo-search (ddgs)`: 無料の検索API
- `arxiv`: arXiv API の Python クライアント
- Google Gemini 2.5 Flash/Pro: 検索結果の要約

---

### 4.3 🔍 インターナルスペシャリスト（社内の情報通）

#### 役割
- 他事業部の類似知見をベクトル検索で探索
- クロスポリネーション（異なる事業部間での知識の横断的な活用）を実現

#### 実装コード

```python
# services/multi_agent.py から抜粋
def agent_internal_specialist(query_text: str, department: str) -> tuple[str, List[dict]]:
    """🔍社内データ検索エージェント。他事業部の知見を検索。"""
    
    # 他事業部の知見を検索（現在の事業部と異なるもののみ）
    hits = backend.search_cross_pollination(query_text, department, top_k=3) or []
    
    if not hits:
        return "関連する社内データが見つかりませんでした。", []
    
    # 検索結果をフォーマット
    bullet_lines = []
    for item in hits:
        metadata = item.get("metadata", {})
        company = metadata.get("company") or "Unknown Company"
        dept = metadata.get("department") or "Unknown Dept"
        content = item.get("content", "")
        bullet_lines.append(f"- {company} ({dept}): {content[:200]}")
    
    result_text = "\n".join(bullet_lines)
    return result_text, hits
```

#### ベクトル検索の実装

```python
# backend.py から抜粋
def search_cross_pollination(query_text: str, current_department: str, top_k: int = 5) -> List[Dict]:
    """他事業部の知見を検索する（現在の事業部と異なるもののみ）"""
    
    # クエリのEmbeddingを取得
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    query_embedding = embeddings.embed_query(query_text)
    
    # Supabaseクライアントを取得
    supabase = get_supabase_client()
    
    # match_documents関数を呼び出し
    response = supabase.rpc(
        "match_documents",
        {
            "query_embedding": query_embedding,
            "match_threshold": 0.0,
            "match_count": 50,  # 多めに取得してからフィルタリング
            "filter": {}
        }
    ).execute()
    
    # 現在の事業部と異なるもののみをフィルタリング
    filtered_results = []
    for result in response.data:
        metadata = result.get("metadata", {})
        department = metadata.get("department", "")
        
        if department != current_department:
            filtered_results.append(result)
    
    # similarityでソート（降順）
    filtered_results.sort(key=lambda x: x.get("similarity", 0.0), reverse=True)
    
    return filtered_results[:top_k]
```

#### 使用技術
- **OpenAI Embeddings API**: テキストをベクトル化
- **Supabase pgvector**: ベクトル検索を実行
- **コサイン類似度**: ベクトル間の類似性を計算

---

### 4.4 💡 ソリューションアーキテクト（発明家）

#### 役割
- 市場データと社内データを統合して提案を作成
- デビルズアドボケイトのフィードバックを踏まえて改善案を作成

#### 実装コード

```python
# services/multi_agent.py から抜粋
def agent_solution_architect(
    market_data: str,
    internal_data: str,
    interview_memo: str,
    feedback: Optional[str] = None,
    model_name: str = "gemini-2.5-flash-lite",
) -> str:
    """💡ソリューションアーキテクトエージェント。市場データと社内データを統合して提案を作成。"""
    
    llm = get_llm(temperature=0.9, streaming=True, model_name=model_name)
    
    prompt = (
        "You are a Genius Solution Architect in a chemical company. Combine the following "
        "\"Internal Data\" and \"Market Facts\" to solve the \"Customer Dilemma\" described in the Interview Memo.\n\n"
        "Constraints:\n"
        "Do NOT just propose existing products. Create a \"Chemical Reaction\" (new combination).\n"
        "If feedback is provided, you MUST revise your proposal to address the criticism.\n"
        "Respond in Japanese only.\n\n"
        f"Internal Data:\n{internal_data}\n\n"
        f"Market Facts:\n{market_data}\n\n"
        f"Interview Memo (Customer Dilemma):\n{interview_memo}\n\n"
        f"Feedback (if any):\n{feedback or 'None'}\n\n"
        "Respond with a concrete proposal."
    )
    
    # ストリーミング出力
    return _stream_response(llm, [HumanMessage(content=prompt)], avatar=SOLUTION_ARCHITECT_AVATAR)
```

#### 使用AI
- Google Gemini 2.5 Flash/Pro
- `temperature=0.9`: 創造性を高めるために高めの温度設定
- `streaming=True`: リアルタイムでの出力表示

---

### 4.5 👿 デビルズアドボケイト（鬼の査読官）

#### 役割
- 提案のリスクと課題を厳しく指摘
- 化学リスク（水解、熱劣化）、コスト実現性、量産問題を検証

#### 実装コード

```python
# services/multi_agent.py から抜粋
def agent_devils_advocate(proposal: str, model_name: str = "gemini-2.5-flash-lite") -> str:
    """👿悪魔の擁護者エージェント。提案を厳しく批判。"""
    
    llm = get_llm(temperature=0.5, streaming=True, model_name=model_name)
    prompt = (
        "You are a Devil's Advocate (Strict Technical Reviewer) inside the proposing company. "
        "Write as an internal reviewer (use 「当社」「当方」「我々」) and never from the client's perspective "
        "(avoid 「貴社/御社」「お客様」等). Criticize the following proposal ruthlessly. Focus on:\n\n"
        "Chemical Risks (Hydrolysis, Heat degradation)\n"
        "Cost Feasibility\n"
        "Mass Production Issues\n\n"
        "Respond in Japanese only, concise bullet style if suitable.\n\n"
        f"Proposal: {proposal}"
    )
    
    return _stream_response(llm, [HumanMessage(content=prompt)], avatar=DEVILS_ADVOCATE_AVATAR)
```

#### 使用AI
- Google Gemini 2.5 Flash/Pro
- `temperature=0.5`: バランスの取れた批判的思考

---

### 4.6 最終レポート統合

#### 役割
オーケストレーターが、すべての議論を統合して最終レポートを作成します。

#### 実装コード

```python
# services/multi_agent.py から抜粋
def agent_orchestrator_summary(
    proposal: str,
    market_data: str,
    internal_data: str,
    interview_memo: str,
    tech_tags: List[str],
    company_name: str,
    model_name: str = "gemini-2.5-flash-lite",
) -> str:
    """👑要約エージェント。指定テンプレートに沿って最終レポートを作成。"""
    
    llm = get_llm(temperature=0.5, model_name=model_name)
    
    # services/report_generator.pyのプロンプトを使用
    system_prompt = REPORT_SYSTEM_PROMPT
    human_prompt = REPORT_HUMAN_PROMPT.format(
        company_name=company_name,
        interview_content=interview_memo,
        tech_tags="、".join(tech_tags),
        cross_link_text=internal_data,
        market_trends=market_data,
        proposal=proposal
    )
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt),
    ]
    
    response = llm.invoke(messages)
    return response.content.strip()
```

#### レポート構成

```markdown
## Trigger
今回の顧客の声（企業名・ニーズ）

## Chemical Insight
抽出された化学的課題

## Cross-Link
社内の他事業部にある類似知見（関連度とその理由）

## Market Trend
関連する市場の動き（競合、市場規模、トレンド、特許、学術論文）

## Proposal
クラレとして提案すべき「新用途」または「改良アイデア」
```

---

## ステップ5：レポート表示

### 概要
生成されたレポートをMarkdown形式で表示し、他事業部の類似知見や学術論文情報をカード形式で表示します。また、LINE風UIで会話ログをリアルタイム表示します。

### 実装ファイル
- `components/idea_report.py`: アイデア創出レポート表示
- `components/conversation_log.py`: イノベーション分隊の会話ログ表示
- `services/slide_report2.py`: スライド生成機能

### 表示内容

1. **戦略レポート（Markdown形式）**
   - Trigger、Chemical Insight、Cross-Link、Market Trend、Proposal

2. **他事業部の類似知見（カード形式）**
   - 企業名、事業部、関連度、内容要約

3. **学術論文情報（カード形式）**
   - タイトル、著者、公開日、リンク、要約

4. **会話ログ（LINE風UI）**
   - 各エージェントの発言をリアルタイム表示
   - アバター画像で視覚的に識別

5. **スライド生成**
   - HTML形式のスライド（Reveal.js）を生成
   - プレビュー機能付き
   - ダウンロード可能

### コード例

```python
# components/idea_report.py から抜粋（簡略版）
def render_idea_report():
    """アイデア創出レポートを表示"""
    
    # セッションから最終レポートを取得
    final_report = st.session_state.get("final_report", "")
    
    if not final_report:
        st.info("まだレポートが生成されていません。")
        return
    
    # Markdownでレポートを表示
    st.markdown(final_report)
    
    # 他事業部の類似知見をカード形式で表示
    st.subheader("🔗 他事業部の類似知見")
    internal_hits = st.session_state.get("internal_hits", [])
    
    for i, hit in enumerate(internal_hits, 1):
        metadata = hit.get("metadata", {})
        company = metadata.get("company", "不明")
        dept = metadata.get("department", "不明")
        similarity = hit.get("similarity", 0.0)
        content = hit.get("content", "")
        
        with st.expander(f"📄 {i}. {company} ({dept}) - 関連度: {similarity:.2%}"):
            st.write(content)
    
    # 学術論文情報をカード形式で表示
    st.subheader("📚 関連学術論文")
    academic_results = st.session_state.get("academic_results", [])
    
    for i, paper in enumerate(academic_results, 1):
        with st.expander(f"📖 {i}. {paper['title']}"):
            st.write(f"**著者**: {', '.join(paper['authors'])}")
            st.write(f"**公開日**: {paper['published']}")
            st.write(f"**リンク**: {paper['link']}")
            st.write(f"**要約**: {paper['summary']}")
```

### LINE風UIの実装

```python
# components/conversation_log.py から抜粋
def render_conversation_log():
    """LINE風UIで会話ログを表示"""
    
    # CSSを注入
    st.markdown(get_chat_css(), unsafe_allow_html=True)
    
    # 会話ログを取得
    conversation_log = st.session_state.get("conversation_log", [])
    
    if not conversation_log:
        st.info("まだ会話ログがありません。")
        return
    
    # 各メッセージを表示
    for message in conversation_log:
        role = message.get("role")
        avatar = message.get("avatar")
        content = message.get("content")
        
        # HTMLでメッセージを表示
        st.markdown(render_message_html(role, avatar, content), unsafe_allow_html=True)


def render_message_html(role: str, avatar: str, content: str) -> str:
    """メッセージのHTMLを生成"""
    
    # アバター画像をBase64エンコード
    avatar_base64 = image_to_base64(avatar)
    
    # HTMLテンプレート
    html = f"""
    <div class="message-container {role}">
        <div class="avatar">
            <img src="data:image/png;base64,{avatar_base64}" alt="avatar">
        </div>
        <div class="message-content">
            <div class="message-bubble">
                {content}
            </div>
        </div>
    </div>
    """
    return html
```

### スライド生成

```python
# services/slide_report2.py から抜粋（簡略版）
def generate_slide_html(report_md: str, company_name: str) -> str:
    """Reveal.js形式のHTMLスライドを生成"""
    
    # Markdownをセクションに分割
    sections = parse_markdown_sections(report_md)
    
    # HTMLテンプレート
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{company_name} - 戦略レポート</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@4/dist/reveal.css">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@4/dist/theme/black.css">
    </head>
    <body>
        <div class="reveal">
            <div class="slides">
                <section>
                    <h1>{company_name}</h1>
                    <h2>戦略レポート</h2>
                </section>
                {generate_slides_from_sections(sections)}
            </div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/reveal.js@4/dist/reveal.js"></script>
        <script>
            Reveal.initialize();
        </script>
    </body>
    </html>
    """
    return html
```

---

## 使用技術とライブラリ一覧

### AI・機械学習

| 技術/サービス | 用途 | 使用箇所 |
|--------------|------|---------|
| **Google Gemini 2.5 Flash/Pro** | AIレビュー、イノベーション分隊の各エージェント、レポート生成 | `services/ai_review.py`<br>`services/multi_agent.py`<br>`services/report_generator.py` |
| **OpenAI Embeddings API**<br>`text-embedding-3-small` | テキストのベクトル化（1536次元） | `backend.py` |

### データベース

| 技術/サービス | 用途 | 使用箇所 |
|--------------|------|---------|
| **Supabase**<br>(PostgreSQL + pgvector) | 面談録の保存、ベクトル検索、メタデータ管理 | `backend.py` |

### 外部API

| API/サービス | 用途 | 使用箇所 |
|-------------|------|---------|
| **DuckDuckGo Search** | 市場トレンド検索、Google Patents検索 | `backend.py`<br>`services/patents.py` |
| **arXiv API** | 学術論文検索 | `services/academic.py` |

### Pythonライブラリ

#### フレームワーク

```python
streamlit>=1.28.0              # Webアプリケーションフレームワーク
```

#### AI・機械学習

```python
langchain>=0.1.0               # LLM統合フレームワーク
langchain-community>=0.0.20    # LangChainコミュニティパッケージ
langchain-openai>=0.0.5        # OpenAI統合
langchain-core>=0.1.0          # LangChainコア機能
langchain-google-genai>=0.1.0  # Google Gemini統合
openai>=1.0.0                  # OpenAI APIクライアント
pydantic>=2.0.0                # データ検証・構造化
```

#### データベース

```python
supabase>=2.0.0                # Supabaseクライアント
```

#### 外部API・検索

```python
duckduckgo-search>=5.0.0       # DuckDuckGo検索API
ddgs>=1.0.0                    # DuckDuckGo検索APIの互換性
arxiv>=2.1.0                   # arXiv API クライアント
```

#### ユーティリティ

```python
python-dotenv>=1.0.0           # 環境変数管理
markdown>=3.0.0                # Markdown処理
python-docx>=1.0.0             # Word文書の読み込み
pypdf>=3.0.0                   # PDF文書の読み込み
```

---

## 技術的なポイントまとめ

### 1. マルチエージェントシステム
- 5人のAIエージェントが役割分担して議論
- 各エージェントは異なる専門性を持つ
- LangChainの`ChatGoogleGenerativeAI`を使用

### 2. ベクトル検索（RAG）
- OpenAI Embeddings APIでテキストをベクトル化
- Supabase pgvectorでコサイン類似度検索
- クロスポリネーション（異なる事業部間での知識共有）を実現

### 3. プロンプトエンジニアリング
- 各エージェントの役割を明確に定義
- 構造化出力（Pydantic）で結果を一貫性のある形式に
- `temperature`パラメータで創造性と正確性を調整

### 4. ストリーミング出力
- LLMの出力をリアルタイムで表示
- `streaming=True`オプションを使用
- LINE風UIで会話ログを視覚的に表示

### 5. データ管理
- Supabaseで面談録を永続化
- メタデータ（企業名、事業部、技術タグ）で検索・フィルタリング
- セッションステートで一時的なデータを管理

### 6. 外部API統合
- DuckDuckGo検索で最新の市場トレンドを取得
- arXiv APIで学術論文を検索
- Google Patentsで特許情報を検索
- エラーハンドリングとフォールバック処理を実装

---

## まとめ

このシステムは、以下の技術を組み合わせて、顧客の面談録から戦略的なアイデアを自動生成します：

1. **AI技術**：Google Gemini、OpenAI Embeddings
2. **データベース**：Supabase（PostgreSQL + pgvector）
3. **外部API**：DuckDuckGo、arXiv、Google Patents
4. **フレームワーク**：Streamlit、LangChain
5. **アーキテクチャ**：マルチエージェントシステム、RAG（Retrieval-Augmented Generation）

これにより、営業担当者は面談内容を入力するだけで、AIが自動的に市場調査、社内知見の検索、提案の作成、批判的レビュー、最終レポートの生成まで行い、戦略的なアイデアを短時間で得ることができます。
