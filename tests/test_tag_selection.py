#!/usr/bin/env python3
"""
技術タグの重要度選定機能のテストスクリプト
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

# 環境変数の読み込み
from dotenv import load_dotenv
load_dotenv()

# アプリのモジュールをインポート
from services.ai_review import select_important_tags


def print_separator(char="=", length=80):
    """区切り線を表示"""
    print(char * length)


def print_section(title: str):
    """セクションタイトルを表示"""
    print_separator()
    print(f"  {title}")
    print_separator()


def test_tag_selection(tech_tags: List[str], interview_memo: str = "", max_tags: int = 5):
    """技術タグの重要度選定をテスト"""
    print_section("技術タグの重要度選定テスト")
    
    print(f"元の技術タグ数: {len(tech_tags)}")
    print(f"元の技術タグ: {', '.join(tech_tags)}")
    print()
    
    if interview_memo:
        print(f"面談メモ（最初の200文字）: {interview_memo[:200]}...")
        print()
    
    try:
        selected_tags = select_important_tags(tech_tags, interview_memo=interview_memo, max_tags=max_tags)
        
        print(f"✅ 選定されたタグ数: {len(selected_tags)}")
        print(f"選定されたタグ: {', '.join(selected_tags)}")
        print()
        
        # クエリの構築例を表示
        academic_query = " ".join(selected_tags)
        patent_query = f"site:patents.google.com {academic_query} 2024 2025"
        market_query = f"{', '.join(selected_tags)} 市場トレンド 規制 新技術 2024 2025"
        
        print("📋 構築されるクエリの例:")
        print(f"  学術論文検索: '{academic_query}' ({len(academic_query)}文字)")
        print(f"  特許検索: '{patent_query[:100]}...' ({len(patent_query)}文字)")
        print(f"  市場トレンド検索: '{market_query[:100]}...' ({len(market_query)}文字)")
        print()
        
        return selected_tags
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return []


def main():
    """メイン関数"""
    print("\n" + "=" * 80)
    print("  技術タグの重要度選定機能のテスト")
    print("=" * 80 + "\n")
    
    # テストケース1: 半導体リソグラフィ関連のタグ
    print("【テストケース1】半導体リソグラフィ関連のタグ")
    tech_tags_1 = [
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
    interview_memo_1 = "半導体リソグラフィにおけるEUVレジスト材料の開発。2nmプロセスノードに対応する高解像度・高感度・低LWRのレジスト材料が求められています。"
    
    selected_1 = test_tag_selection(tech_tags_1, interview_memo_1, max_tags=5)
    print()
    
    # テストケース2: ポリマー材料関連のタグ
    print("【テストケース2】ポリマー材料関連のタグ")
    tech_tags_2 = [
        "polymer",
        "heat resistance",
        "automotive",
        "耐熱性",
        "ポリマー",
        "自動車部品",
        "120度",
        "強度",
        "コスト",
        "量産",
        "成形性",
        "耐候性"
    ]
    interview_memo_2 = "顧客から高温環境下でも劣化しないポリマー材料の開発依頼がありました。現在使用している材料は120度以上の温度で強度が低下する問題があります。自動車部品への応用を想定しており、耐熱性とコストのバランスが重要です。"
    
    selected_2 = test_tag_selection(tech_tags_2, interview_memo_2, max_tags=5)
    print()
    
    # テストケース3: タグが5つ以下の場合
    print("【テストケース3】タグが5つ以下の場合")
    tech_tags_3 = ["polymer", "heat resistance", "automotive"]
    selected_3 = test_tag_selection(tech_tags_3, "", max_tags=5)
    print()
    
    # 結果サマリー
    print_separator()
    print("テスト結果サマリー")
    print_separator()
    
    print(f"テストケース1: {len(selected_1)}個のタグを選定")
    print(f"テストケース2: {len(selected_2)}個のタグを選定")
    print(f"テストケース3: {len(selected_3)}個のタグを選定")
    print()
    
    all_passed = all([
        len(selected_1) == 5,
        len(selected_2) == 5,
        len(selected_3) <= 5
    ])
    
    if all_passed:
        print("✅ すべてのテストが成功しました。")
    else:
        print("⚠️  一部のテストで問題が発生しました。")
    
    print_separator()
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

