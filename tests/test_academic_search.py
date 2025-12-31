#!/usr/bin/env python3
"""
学術論文検索機能のテスト・確認用スクリプト

使用方法:
    python test_academic_search.py
    python test_academic_search.py --query "polymer heat resistance"
    python test_academic_search.py --query "機械学習" --max-results 10
"""

import argparse
import sys
import json
from typing import List, Dict

# ログ設定
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from services.academic import search_arxiv, format_arxiv_results


def print_separator():
    """区切り線を表示"""
    print("=" * 80)


def test_basic_search(query: str, max_results: int = 5):
    """基本的な検索テスト"""
    print_separator()
    print(f"テスト1: 基本的な検索")
    print(f"クエリ: '{query}'")
    print(f"最大取得件数: {max_results}")
    print_separator()
    
    try:
        results = search_arxiv(query, max_results)
        
        if not results:
            print("❌ 検索結果がありませんでした。")
            return False
        
        print(f"✅ {len(results)}件の論文を取得しました。\n")
        
        # 詳細表示
        for i, paper in enumerate(results, 1):
            print(f"【論文{i}】")
            print(f"  タイトル: {paper['title']}")
            print(f"  著者: {', '.join(paper['authors'])}")
            print(f"  公開日: {paper['published']}")
            print(f"  リンク: {paper['link']}")
            print(f"  要約（最初の200文字）: {paper['summary'][:200]}...")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_format_function(results: List[Dict]):
    """フォーマット関数のテスト"""
    print_separator()
    print("テスト2: フォーマット関数のテスト")
    print_separator()
    
    formatted = format_arxiv_results(results)
    print(formatted)
    print()
    
    return formatted


def test_empty_results():
    """空の結果のテスト"""
    print_separator()
    print("テスト3: 空の結果のテスト")
    print_separator()
    
    formatted = format_arxiv_results([])
    print(f"空の結果のフォーマット: '{formatted}'")
    print()
    
    return formatted == "学術論文は見つかりませんでした。"


def test_json_output(query: str, max_results: int = 3):
    """JSON形式での出力テスト"""
    print_separator()
    print("テスト4: JSON形式での出力")
    print(f"クエリ: '{query}'")
    print_separator()
    
    try:
        results = search_arxiv(query, max_results)
        
        if results:
            print("JSON形式:")
            print(json.dumps(results, ensure_ascii=False, indent=2))
            print()
            return True
        else:
            print("❌ 検索結果がありませんでした。")
            return False
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return False


def test_error_handling():
    """エラーハンドリングのテスト"""
    print_separator()
    print("テスト5: エラーハンドリングのテスト")
    print_separator()
    
    # 無効なクエリ（空文字列）
    try:
        results = search_arxiv("", max_results=1)
        print(f"空文字列クエリの結果: {len(results)}件")
        print("✅ エラーなく処理されました（空の結果を返す）")
        print()
        return True
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return False


def run_all_tests(query: str = "polymer", max_results: int = 5):
    """すべてのテストを実行"""
    print("\n" + "=" * 80)
    print("学術論文検索機能のテスト開始")
    print("=" * 80 + "\n")
    
    test_results = []
    
    # テスト1: 基本的な検索
    result1 = test_basic_search(query, max_results)
    test_results.append(("基本的な検索", result1))
    
    if result1:
        # テスト2: フォーマット関数
        results = search_arxiv(query, max_results)
        result2 = test_format_function(results)
        test_results.append(("フォーマット関数", result2))
        
        # テスト4: JSON出力
        result4 = test_json_output(query, min(max_results, 3))
        test_results.append(("JSON出力", result4))
    
    # テスト3: 空の結果
    result3 = test_empty_results()
    test_results.append(("空の結果", result3))
    
    # テスト5: エラーハンドリング
    result5 = test_error_handling()
    test_results.append(("エラーハンドリング", result5))
    
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


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="学術論文検索機能のテスト・確認用スクリプト"
    )
    parser.add_argument(
        "--query",
        type=str,
        default="polymer",
        help="検索クエリ（デフォルト: 'polymer'）"
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=5,
        help="最大取得件数（デフォルト: 5）"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="クイックテスト（基本的な検索のみ）"
    )
    
    args = parser.parse_args()
    
    if args.quick:
        # クイックテスト
        print(f"\nクイックテスト: '{args.query}' で検索\n")
        success = test_basic_search(args.query, args.max_results)
        sys.exit(0 if success else 1)
    else:
        # 全テスト実行
        success = run_all_tests(args.query, args.max_results)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

