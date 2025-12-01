# R&D Brain フロー図

```
[User/営業]
  |
  | 入力: 企業名・部署/役職・面談メモ
  v
[Streamlit UI (components)]
  - sidebar.py: 事業部選択＋APIキー確認
  - interview_form.py: フォーム送信→レビュー開始
  |
  | 面談メモ
  v
[AIレビュー (services/ai_review.py, GPT-4o)]
  - 情報十分判定 / 追加質問
  - 要約 / 技術タグ抽出
  |
  | ReviewResult(十分判定/タグ)
  v
[レビュー結果表示 (components/review_results.py)]
  - OKなら「登録」ボタン表示
  |
  | メタデータ付与(事業部・会社・タグ・timestamp)
  v
[保存 (backend.save_interview_note)]
  - text-embedding-3-smallで埋め込み
  - Supabase documentsテーブルへ保存
  |
  | (保存成功後 自動起動)
  v
[アイデア創出マルチエージェント (services/multi_agent.py, Gemini)]
  1) 司会ブリーフ生成
  2) 市場調査: backend.search_market_trends + services.patents + services.academic
  3) 社内知見検索: backend.search_cross_pollination (他事業部のみ)
  4) 提案作成 → 悪魔の代弁者で批評 → 改訂案
  5) 最終Markdownレポート生成 (services.report_generator)
  |
  | 最終レポートMarkdown, クロスポリ結果
  v
[レポート表示・出力 (components/idea_report.py)]
  - Markdown表示＋他事業部カード
  - 変換: google_slide/markdown_parser
  - HTML出力: services/html_report → outputs/*.html
  - スライド出力: services/slide_report → outputs/slide-*.html
  - リセットボタンで新規入力へ戻る
```

- キー環境変数: `SUPABASE_URL`, `SUPABASE_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`
