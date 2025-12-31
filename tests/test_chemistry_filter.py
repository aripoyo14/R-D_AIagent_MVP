#!/usr/bin/env python3
"""
化学関連フィルタのテストスクリプト
"""

import sys
from services.academic import search_arxiv

def test_chemistry_filter():
    """化学関連フィルタのテスト"""
    print("=" * 80)
    print("化学関連フィルタのテスト")
    print("=" * 80 + "\n")
    
    # テストケース1: アンモニア
    print("【テストケース1】アンモニア")
    print("-" * 80)
    results = search_arxiv("ammonia", max_results=5)
    print(f"取得件数: {len(results)}")
    for i, paper in enumerate(results, 1):
        print(f"{i}. {paper['title']}")
        print(f"   カテゴリ: {', '.join(paper.get('categories', [])[:3])}")
    print()
    
    # テストケース2: ポリマー
    print("【テストケース2】ポリマー")
    print("-" * 80)
    results = search_arxiv("polymer", max_results=5)
    print(f"取得件数: {len(results)}")
    for i, paper in enumerate(results, 1):
        print(f"{i}. {paper['title']}")
        print(f"   カテゴリ: {', '.join(paper.get('categories', [])[:3])}")
    print()
    
    # テストケース3: 日本語キーワード
    print("【テストケース3】日本語キーワード（アンモニア）")
    print("-" * 80)
    results = search_arxiv("アンモニア", max_results=5)
    print(f"取得件数: {len(results)}")
    for i, paper in enumerate(results, 1):
        print(f"{i}. {paper['title']}")
    print()
    
    print("=" * 80)
    print("テスト完了")
    print("=" * 80)

if __name__ == "__main__":
    test_chemistry_filter()

