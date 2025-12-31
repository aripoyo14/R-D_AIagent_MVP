#!/usr/bin/env python3
"""
特定の技術タグパターンでのテストスクリプト

半導体リソグラフィ関連の技術タグでの検索テスト
"""

import sys
import os
from typing import List

# ログ設定
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Streamlitのモック
class MockStreamlit:
    class ChatMessage:
        def __init__(self, role, avatar=None):
            self.role = role
            self.avatar = avatar
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
    
    @staticmethod
    def chat_message(role, avatar=None):
        return MockStreamlit.ChatMessage(role, avatar)
    
    @staticmethod
    def markdown(text):
        print(f"[Streamlit] {text}")
    
    @staticmethod
    def empty():
        class Empty:
            def markdown(self, text):
                print(f"[Streamlit Empty] {text}")
        return Empty()

sys.modules['streamlit'] = type(sys)('streamlit')
import streamlit as st
st.chat_message = MockStreamlit.chat_message
st.markdown = MockStreamlit.markdown
st.empty = MockStreamlit.empty

# 環境変数の読み込み
from dotenv import load_dotenv
load_dotenv()

# アプリのモジュールをインポート
from services.academic import search_arxiv, format_arxiv_results
from services.patents import search_patents
from backend import search_market_trends
from services.multi_agent import agent_market_researcher


def print_separator(char="=", length=80):
    """区切り線を表示"""
    print(char * length)


def print_section(title: str):
    """セクションタイトルを表示"""
    print_separator()
    print(f"  {title}")
    print_separator()


def test_query_construction(tech_tags: List[str]):
    """クエリ構築の確認"""
    print_section("クエリ構築の確認")
    
    # 学術論文検索のクエリ
    academic_query = " ".join(tech_tags)
    print(f"📚 学術論文検索クエリ:")
    print(f"   '{academic_query}'")
    print(f"   長さ: {len(academic_query)}文字")
    print()
    
    # 特許検索のクエリ
    patent_query = f"site:patents.google.com {' '.join(tech_tags)} 2024 2025"
    print(f"🔍 特許検索クエリ:")
    print(f"   '{patent_query}'")
    print(f"   長さ: {len(patent_query)}文字")
    print()
    
    # 市場トレンド検索のクエリ
    tags_str = ", ".join(tech_tags)
    use_case = "半導体リソグラフィにおけるEUVレジスト材料の開発"
    use_case_trimmed = " ".join(use_case.split())[:180] if use_case else ""
    query_parts = [tags_str, use_case_trimmed, "市場トレンド 規制 新技術 2024 2025"]
    market_query = " ".join([p for p in query_parts if p]).strip()[:512]
    print(f"📊 市場トレンド検索クエリ:")
    print(f"   '{market_query}'")
    print(f"   長さ: {len(market_query)}文字")
    print()


def test_academic_search(tech_tags: List[str]):
    """学術論文検索のテスト"""
    print_section("学術論文検索のテスト")
    
    query = " ".join(tech_tags)
    print(f"検索クエリ: '{query}'")
    print()
    
    try:
        results = search_arxiv(query, max_results=5)
        
        if not results:
            print("⚠️  学術論文が見つかりませんでした。")
            return False
        
        print(f"✅ {len(results)}件の学術論文を取得しました。\n")
        
        for i, paper in enumerate(results, 1):
            print(f"【論文{i}】")
            print(f"  タイトル: {paper['title']}")
            print(f"  著者: {', '.join(paper['authors'][:3])}{'...' if len(paper['authors']) > 3 else ''}")
            print(f"  公開日: {paper['published']}")
            print(f"  リンク: {paper['link']}")
            print()
        
        # フォーマット関数のテスト
        formatted = format_arxiv_results(results)
        print("📝 フォーマット後の文字列（最初の500文字）:")
        print("-" * 80)
        print(formatted[:500] + "..." if len(formatted) > 500 else formatted)
        print("-" * 80)
        print()
        
        return True
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
        print(f"❌ エラー: {e}")
        return False


def test_patent_search(tech_tags: List[str]):
    """特許検索のテスト"""
    print_section("特許検索のテスト")
    
    print(f"技術タグ: {tech_tags}")
    print()
    
    try:
        results = search_patents(tech_tags, max_results=5)
        
        if not results or "見つかりませんでした" in results:
            print("⚠️  特許情報が見つかりませんでした。")
            return False
        
        print("✅ 特許検索が完了しました。\n")
        print("📋 検索結果（最初の1000文字）:")
        print("-" * 80)
        print(results[:1000] + "..." if len(results) > 1000 else results)
        print("-" * 80)
        print()
        
        return True
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
        print(f"❌ エラー: {e}")
        return False


def test_market_trends_search(tech_tags: List[str]):
    """市場トレンド検索のテスト"""
    print_section("市場トレンド検索のテスト")
    
    use_case = "半導体リソグラフィにおけるEUVレジスト材料の開発。2nmプロセスノードに対応する高解像度・高感度・低LWRのレジスト材料が求められています。"
    
    print(f"技術タグ: {tech_tags}")
    print(f"用途: {use_case}")
    print()
    
    try:
        results = search_market_trends(tech_tags, use_case)
        
        if not results or "見つかりませんでした" in results:
            print("⚠️  市場情報が見つかりませんでした。")
            return False
        
        print("✅ 市場トレンド検索が完了しました。\n")
        print("📋 検索結果（最初の1000文字）:")
        print("-" * 80)
        print(results[:1000] + "..." if len(results) > 1000 else results)
        print("-" * 80)
        print()
        
        return True
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
        print(f"❌ エラー: {e}")
        return False


def test_market_researcher_agent(tech_tags: List[str]):
    """市場調査エージェント全体のテスト"""
    print_section("市場調査エージェント全体のテスト")
    
    use_case = "半導体リソグラフィにおけるEUVレジスト材料の開発。2nmプロセスノードに対応する高解像度・高感度・低LWRのレジスト材料が求められています。"
    
    print(f"技術タグ: {tech_tags}")
    print(f"用途: {use_case[:100]}...")
    print()
    
    try:
        print("🔍 市場調査エージェントを実行中...")
        summary = agent_market_researcher(tech_tags, use_case)
        
        if not summary:
            print("❌ 市場調査エージェントが結果を返しませんでした。")
            return False
        
        print("✅ 市場調査エージェントが完了しました。\n")
        print("📊 市場調査サマリー（最初の2000文字）:")
        print("-" * 80)
        print(summary[:2000] + "..." if len(summary) > 2000 else summary)
        print("-" * 80)
        print()
        
        # 学術論文の情報が含まれているか確認
        if "論文" in summary or "academic" in summary.lower() or "研究" in summary or "arxiv" in summary.lower():
            print("✅ 学術論文の情報が市場調査サマリーに含まれています。")
        else:
            print("⚠️  学術論文の情報が市場調査サマリーに明示的に含まれていない可能性があります。")
        
        return True
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """メイン関数"""
    # 技術タグの定義
    tech_tags = [
        "EUVレジスト",
        "メタル酸化物レジスト",
        "MOR",
        "2nmプロセスノード",
        "半導体リソグラフィ",
        "高解像度",
        "高感度",
        "低LWR",
        "ライン幅ラフネス",
        "低アウトガス",
        "高純度材料",
        "パターン倒壊耐性",
        "有機溶剤現像",
        "NTD",
        "確率的欠陥",
        "Stochastics",
        "RLSトレードオフ",
        "フォトレジスト",
        "有機ハイブリッド材料"
    ]
    
    print("\n" + "=" * 80)
    print("  特定技術タグパターンでの検索テスト")
    print("=" * 80 + "\n")
    
    print(f"技術タグ数: {len(tech_tags)}")
    print(f"技術タグ: {', '.join(tech_tags[:5])}... (他{len(tech_tags)-5}件)")
    print()
    
    test_results = []
    
    # 1. クエリ構築の確認
    test_query_construction(tech_tags)
    
    # 2. 学術論文検索のテスト
    result1 = test_academic_search(tech_tags)
    test_results.append(("学術論文検索", result1))
    
    # 3. 特許検索のテスト
    result2 = test_patent_search(tech_tags)
    test_results.append(("特許検索", result2))
    
    # 4. 市場トレンド検索のテスト
    result3 = test_market_trends_search(tech_tags)
    test_results.append(("市場トレンド検索", result3))
    
    # 5. 市場調査エージェント全体のテスト
    result4 = test_market_researcher_agent(tech_tags)
    test_results.append(("市場調査エージェント", result4))
    
    # 結果サマリー
    print_separator()
    print("テスト結果サマリー")
    print_separator()
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n合計: {passed}/{total} テストが成功しました。")
    print_separator()
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

