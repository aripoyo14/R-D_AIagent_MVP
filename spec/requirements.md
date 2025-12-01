# 要件定義

## 1. システム概要
- 面談メモを起点に、社内知見＋外部情報を統合し、5人のAIエージェント（Innovation Squad）がチャット形式で議論し最終レポートを生成。
- 旧シングルショット生成（services/report_generator.py）は廃止し、services/multi_agent.py が新コア。

## 2. 既存資産の再利用範囲
- データベース: Supabaseベクトルストア（backend.py）。
- 入力IF: Streamlitフォーム＋AI事前レビュー（components/interview_form.py, services/ai_review.py）。
- 検索ツール群: 特許/論文/ニュース検索モジュール（services/*.py）。
- UI: サイドバー、設定、レポートカード（components/*）。

## 3. 新規・変更要件
- AI処理: 5エージェント対話型生成（services/multi_agent.py）。
- UX: 処理待ちを「チャット観戦」に変更。Orchestrator, Market Researcher, Internal Specialist, Solution Architect, Devil's Advocate の会話をリアルタイム表示。
- report_generator.py は参照のみ、呼び出し停止。

## 4. 既存APIの利用
- backend.py
  - search_market_trends(tech_tags, use_case): 市場・規制・競合検索（Market Researcher）。
  - search_cross_pollination(query_text, current_department, top_k): 社内類似知見検索（Internal Specialist）。
  - save_interview_note(text, metadata): 面談録保存（AIレビュー後、エージェント前）。
- services/ai_review.py: review_interview_content(content) 面談メモ具体性チェック（送信直後）。
- オプションツール: services/patents.search_patents, services/academic.search_arxiv, services/translation.*。

## 5. 新規エージェント設計（services/multi_agent.py）
- 共通: get_llm(temperature) ヘルパーを用意。
- Orchestrator ブリーフ: 面談メモから課題/競合/リスク/納期/各役割への指示を1段落でLLM生成し、冒頭に表示。
- 🤖 Orchestrator (T=0.5): 司会と最終Markdownレポート生成。st.chat_messageで進行描画。
- 🕵️ Market Researcher (T=0.3): search_market_trendsを使用。事実のみ、空なら「情報なし」。
- 🔍 Internal Specialist (T=0.3): search_cross_pollinationを使用。社内知見提示、ヒットなしは「なし」。
- 💡 Solution Architect (T=0.9): CoTで「社内技術×市場ニーズ」の非連続アイデア。st.write_streamで出力。
- 👿 Devil's Advocate (T=0.5): 化学的リスク/コスト/実現性を具体批判。st.write_streamで出力。
- run_innovation_squad: ブリーフ表示→順次呼び出しを制御し、議論を描画、最終レポート返却。

## 6. UI統合（components/review_results.py）
- generate_idea_report → run_innovation_squad に差し替え。
- 「登録」ボタン後、save_interview_note 成功直後に run_innovation_squad を起動。
- 返却レポートを st.session_state.idea_report に保存。

## 7. データモデル・保存メタデータ
- Supabaseテーブル（例: documents）: id, company, department, role, content, tags(json/array), embedding(vector), created_at。
- インデックス/pgvector設定: embedding に ivfflat などの適切な索引、tags/department にフィルタ用索引。
- 保存メタデータ: 面談テキスト、技術タグ、部署/事業部、用途/ユースケース、登録者、温度/物性などの抽出値。

## 8. LLM設定・プロンプトガード
- モデル: Gemini 2.5 Flash 固定（ストリーミング有効）。温度は上記ロール別に設定。
- トークン上限: 1エージェント応答は max_tokens を設定し、全体で枯渇しないよう制限。
- 禁止事項: 推測や事実なき断定を禁止（特に Market Researcher）。ソース明記を促す。守れない場合は「情報なし」。
- ツールフォールバック: DuckDuckGo/ベクトル検索失敗時はスキップしエラーをUI通知、処理は継続。

## 9. 非機能・運用
- レイテンシ: エージェントごとにタイムアウト（例: 20–30s）を設定しハング防止。ストリーミングで体感短縮。
- ログ/可観測性: ツール呼び出し結果概要、失敗理由をログ。PIIはマスク。
- レジリエンス: リトライ回数（1–2回）とバックオフ、ゼロ件結果は正常扱い。
- セキュリティ: APIキーは .env から読み込み。UIにはキー表示しない。

## 10. 失敗時ハンドリング
- 検索ゼロ件: 「情報なし」とチャットに表示、処理継続。
- LLM失敗(Gemini): ユーザーに簡潔なエラー表示＋再実行ボタン（想定）。
- Supabase書き込み失敗: 保存とエージェント起動を中断し、ユーザー通知。
- 例外共通: UIトースト/アラートで可読メッセージ、ログには詳細。

## 11. 状態遷移・UX
- フロー: 入力 → AIレビュー → (OK) 保存 → エージェント進行 → 最終レポート表示。
- ボタン: 保存/エージェント実行中は二重送信防止のdisable。
- チャット表示: st.chat_messageでエージェントごとにアイコン/ロール表示。Architect/Devilはストリーム表示。
- レポート再表示: st.session_state.idea_report に保持しリロードで再利用。

## 12. 実装タスク
- Phase 1: .env の OPENAI_API_KEY/SUPABASE_URL/SUPABASE_KEY 確認。save_interview_note 動作確認。search_market_trends / search_cross_pollination 単体確認。
- Phase 2: multi_agent 実装（ヘルパー、調査/発想/批判エージェント、オーケストレーション、空結果ハンドリング、ストリーミング表示）。
- Phase 3: review_results.py 統合（呼び出し差し替え、トリガー修正、state保存）。
- Phase 4: シナリオテスト（例: 「EVバスバー向けの耐熱絶縁材料が必要」— AI Review OK、チャット進行、800V化等の市場語、PA9T提案、吸水性指摘、最終レポート表示）。

## 13. 受入れ条件/テスト観点
- 正常系: 上記シナリオで全エージェントが発話し、最終Markdownレポートが表示される。
- 検索0件: Market/Internal が「情報なし/なし」で落ちずに完了。
- LLM失敗(Gemini): ユーザーがエラーを確認でき再実行可能。
- Supabase失敗: 保存エラーを表示しエージェント実行を開始しない。
- UI: 二重送信が防止され、チャットの役割表示が正しい。
