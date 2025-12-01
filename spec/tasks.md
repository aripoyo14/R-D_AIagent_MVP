# 実装タスク一覧 (tasks.md)

## Phase 0: 環境前提
- [x] **0-1. 環境変数**: `.env` に `OPENAI_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`, `LLM_PROVIDER`/`LLM_MODEL` を設定（デフォルト openai:gpt-4o、Gemini 2.5 Pro/Flash も可）。
- [x] **0-2. ランタイム**: Python 3.12 以上で `pip install -r requirements.txt` 済み。

## Phase 1: 既存機能の健全性チェック
- [x] **1-1. DB書き込み**: `backend.py` の `save_interview_note` が Supabase に書き込めることを確認。
- [x] **1-2. 市場検索**: `search_market_trends`（DuckDuckGo）が単体で動作することを確認。
- [x] **1-3. 社内知見検索**: `search_cross_pollination`（pgvector）が単体で動作することを確認。
- [x] **1-4. 環境変数チェック**: `.env` キー読み込みエラー時のメッセージ確認。

## Phase 2: multi_agent 実装 (services/multi_agent.py)
- [x] **2-1. Setup**: ファイル作成と `langchain_openai`, `streamlit` 等のインポート。
- [x] **2-2. Helper**: `get_llm(temperature)` ファクトリ（Gemini固定・ストリーミング対応）。
- [x] **2-3. Agent: Market Researcher**: `search_market_trends` 呼び出し、事実のみ、ゼロ件は「情報なし」。
- [x] **2-4. Agent: Internal Specialist**: `search_cross_pollination` 呼び出し、ヒットなしは「なし」。
- [x] **2-5. Agent: Solution Architect**: CoT で非連続アイデア、ストリーミング出力。
- [x] **2-6. Agent: Devil's Advocate**: 化学リスク/コスト/実現性を批判、ストリーミング出力。
- [x] **2-7. Agent: Orchestrator**: 面談メモから司会ブリーフ生成、進行・指示と最終Markdown生成、`st.chat_message` で描画。
- [x] **2-8. Orchestration**: `run_innovation_squad` でブリーフ表示→順次呼び出し、UI描画、ツール失敗時はスキップ＋通知、レポート返却。

## Phase 3: UI統合 (components/review_results.py 他)
- [x] **3-1. 呼び出し差替え**: `generate_idea_report` → `run_innovation_squad`。
- [x] **3-2. トリガー修正**: 「登録」ボタン後、`save_interview_note` 成功直後に実行。
- [x] **3-3. ステート保存**: 最終レポートを `st.session_state.idea_report` に格納し表示コンポーネントで使用。
- [x] **3-4. ボタン状態**: 実行中は disable して二重送信防止。

## Phase 4: LLM/埋め込み設定
- [ ] **4-1. LLM固定**: Gemini 2.5 Flash を使用する設定（`GEMINI_API_KEY` 設定、`LLM_MODEL` で将来バージョン差替え可）。ストリーム不可時はバッファ一括表示にフォールバック。
- [ ] **4-2. 埋め込み**: `text-embedding-3-small` (OpenAI) 前提、`EMBEDDING_MODEL` で差し替え可能にする。

## Phase 5: エラーハンドリング/レジリエンス
- [ ] **5-1. ゼロ件ハンドル**: 検索ゼロ件を「情報なし/なし」で継続。
- [ ] **5-2. LLM失敗**: OpenAI/Gemini 失敗時にUIエラー＋再実行ボタン、ログ記録。
- [ ] **5-3. Supabase失敗**: 保存エラー表示しエージェント未起動。
- [ ] **5-4. タイムアウト/リトライ**: ツール/LLM に 20–30s タイムアウトと必要なら1–2回リトライ。

## Phase 6: テスト/受入れ
- [ ] **6-1. 正常系**: 「EVバスバー向けの耐熱絶縁材料が必要」シナリオで5エージェント発話＋最終レポート表示（Market:800V、Architect:PA9T、Devil:吸水性）。
- [ ] **6-2. 検索0件**: Market/Internal が「情報なし/なし」で完了。
- [ ] **6-3. LLM失敗**: OpenAI/Gemini 失敗時にエラー表示と再実行が機能。
- [ ] **6-4. Supabase失敗**: 保存エラー表示でエージェント未起動。
- [ ] **6-5. UI**: チャットロール表示と二重送信防止が正しく動作。
