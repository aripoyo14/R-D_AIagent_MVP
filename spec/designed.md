# 詳細設計 (designed.md)

## 1. アーキテクチャ概要
- エントリ: `app.py` (Streamlit)。入力フォーム、ステート管理、レビュー結果表示、エージェント実行トリガー。
- コアロジック: `services/multi_agent.py` に5人エージェントの対話ロジックとオーケストレーションを集約。
- ツール群: `backend.py` の Supabase/検索ツールを共通APIとして利用。追加ツールは `services/*.py` からインポートしツール呼び出しで使用。
- データ永続化: Supabase (PostgreSQL + pgvector) で面談記録とベクトルを保存/検索。
- UIコンポーネント: `components/` 配下のフォーム/レビュー/レポートカードを再利用し、`review_results.py` でエージェント出力を描画。

## 2. データモデル (Supabase)
- テーブル例: `documents`
  - `id` (uuid, pk)
  - `company` (text)
  - `department` (text)
  - `role` (text)
  - `content` (text)
  - `tags` (json/array)
  - `use_case` (text)
  - `embedding` (vector)
  - `created_at` (timestamptz, default now)
  - `author` (text)
  - 抽出パラメータ例: 温度/物性などは json で格納可
- インデックス: `embedding` に ivfflat 等の近似索引、`department`/`tags` に btree/GIN でフィルタ高速化。

## 3. コンポーネントと責務
- `app.py`: フォーム表示、`review_interview_content` 実行、結果に応じて `save_interview_note` 呼び出し後 `run_innovation_squad` をトリガー。`st.session_state` にレビュー結果/最終レポートを保持。
- `components/interview_form.py`: 入力フィールド、バリデーション、送信ボタン。送信時にレビューサービスを呼び出すフックを提供。
- `components/review_results.py`: AIレビュー結果表示、保存とエージェント起動ボタン。`generate_idea_report` 呼び出しを `run_innovation_squad` へ差し替え。
- `components/idea_report.py`: 最終レポートカード表示。`st.session_state.idea_report` を参照。
- `services/ai_review.py`: 入力チェック（具体性の有無）。OK/NGと追加質問を返却。
- `backend.py`: `save_interview_note`, `search_market_trends`, `search_cross_pollination` を提供。Supabase/DuckDuckGo/pgvector の薄いラッパー。
- `services/patents.py`, `services/academic.py`, `services/news.py`, `services/translation.py`: 必要時にツール呼び出しで使用可能。

## 4. エージェント設計 (services/multi_agent.py)
- 共通: `get_llm(temperature)` で LLM クライアント取得（ストリーミング対応）。
- 🤖 Orchestrator (T=0.5): 司会、段取り、各エージェント呼び出し。面談メモから課題/競合/リスク/納期/各役割への指示をLLMで1段落生成し冒頭に表示。最終Markdownレポート生成。`st.chat_message` で進行表示。
- 🕵️ Market Researcher (T=0.3): `search_market_trends` を実行し、事実のみ報告。空結果は「情報なし」。
- 🔍 Internal Specialist (T=0.3): `search_cross_pollination` を実行し、他部署の知見を提示。ヒットなしは「なし」。
- 💡 Solution Architect (T=0.9): CoT で「社内技術×市場ニーズ」を結合し非連続アイデア。`st.write_stream` で逐次表示。
- 👿 Devil's Advocate (T=0.5): 化学的リスク/コスト/実現性を具体的に批判。`st.write_stream` で逐次表示。
- `run_innovation_squad`: 入力メモとメタを受け、レビュー済みデータを基に上記エージェントを順次起動。UI描画と最終レポート返却を一手に管理。

## 5. フロー (UX/処理)
1) ユーザーがフォーム入力 → 送信。
2) `review_interview_content` 実行。NGの場合は追加入力を促し終了。OKなら次へ。
3) `save_interview_note` で Supabase 保存（メタ＋embedding）。失敗時はエラー表示し処理停止。
4) `run_innovation_squad` 起動。
   - Orchestrator が面談メモを要約したブリーフ（課題/競合/リスク/納期/役割指示）を表示。
   - Market Researcher → Internal Specialist → Solution Architect → Devil's Advocate → Solution Architect(改訂) の順に発話。
   - 各ツール呼び出し結果をチャットに表示。ゼロ件は「情報なし/なし」で表示。
   - Orchestrator が全結果を統合し Markdown レポート生成。`st.session_state.idea_report` に保存。
5) `components/idea_report.py` で最終レポートカード表示。再訪時は state から再表示。

## 6. LLM設定・ガードレール
- モデル: Gemini 2.5 Flash 固定（ストリーミング有効）。`GEMINI_API_KEY` を必須とし、未設定時はエラーにする。
- フォールバック: ストリーム不可な場合はバッファして一括表示にフォールバック。
- 埋め込みモデル: `text-embedding-3-small` (OpenAI) を前提とし、`EMBEDDING_MODEL` で差し替え可能にする（現状はOpenAI運用を基本としGemini Embeddingsは想定外）。
- 温度: Orchestrator 0.5 / Market 0.3 / Internal 0.3 / Architect 0.9 / Devil 0.5。
- トークン制御: エージェントごとに `max_tokens` を設定し、全体枯渇を防ぐ。
- 禁止事項: 推測・事実なき断定禁止（特に Market）。ソース明記。守れない場合は「情報なし」。
- ツールフォールバック: 検索失敗時はスキップ＋UI通知。例外は握りつぶさずユーザーに可読メッセージ。

## 7. エラーハンドリングとレジリエンス
- 検索0件: 正常扱いで「情報なし」表示。
- LLM失敗(Gemini): 簡潔なエラー表示＋再実行ボタンを想定。ログに詳細。
- Supabase書き込み失敗: エラー表示しエージェント実行を開始しない。
- タイムアウト: ツール/LLMに 20–30s 目安のタイムアウト。必要に応じ1–2回リトライ。
- PII/ログ: ログでは個人情報をマスク。UIでキーは表示しない。

## 8. UX/状態管理
- ボタン状態: 保存中/エージェント実行中は送信ボタンを disable して二重送信防止。
- チャット: `st.chat_message` でロールごとにアイコン/名前を表示。ストリーム表示は Architect/Devil の発想・批判に使用。
- 状態保持: `st.session_state` にレビュー結果、保存メタ、`idea_report` を格納。ブラウザ再読み込み時もレポート再表示可。

## 9. 受入れ・テスト観点
- 正常系: 「EVバスバー向けの耐熱絶縁材料が必要」でエージェントが発話し、Market が 800V 化等を返し、Architect が PA9T 等を提案、Devil が吸水性などを指摘、最終レポート表示。
- 検索0件: Market/Internal が「情報なし/なし」で落ちずに完了。
- OpenAI失敗: エラー表示され再実行可能。
- Supabase失敗: 保存エラーが表示されエージェントが起動しない。
- UI: チャットのロール表示と二重送信防止が効いている。

## 10. 実装メモ/移行
- `services/report_generator.py` は参照のみ。新規呼び出しは禁止。
- 既存コンポーネント/スタイルは踏襲し、UX変更はチャット観戦体験の追加に限定。
- `.env`: `OPENAI_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY` を必須とし、設定チェックを起動前に行う。
- ランタイム: Python 3.12 以上を前提（requirements.txt 準拠）。
- LLMモデル: Gemini 2.5 Flash 固定。`GEMINI_API_KEY` を必須とし、`LLM_MODEL` で将来の Gemini バージョンに差し替え可能とする。
