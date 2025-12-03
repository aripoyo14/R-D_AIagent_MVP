#!/usr/bin/env python3
"""
特許検索機能のテストスクリプト

使用方法:
    python test_patents.py
    python test_patents.py --keywords "polymer" "heat resistance"
    python test_patents.py --keywords "樹脂" "耐熱" --max-results 10 --debug
"""

import argparse
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from services.patents import search_patents


def main():
    parser = argparse.ArgumentParser(
        description="特許検索機能のテストスクリプト",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # デフォルトのキーワードでテスト
  python test_patents.py

  # カスタムキーワードでテスト
  python test_patents.py --keywords "polymer" "heat resistance"

  # デバッグモードで詳細情報を表示
  python test_patents.py --keywords "樹脂" "耐熱" --max-results 10 --debug
        """
    )
    
    parser.add_argument(
        "--keywords",
        nargs="+",
        default=["polymer", "heat", "resistance"],
        help="検索キーワード（デフォルト: polymer heat resistance）"
    )
    
    parser.add_argument(
        "--max-results",
        type=int,
        default=5,
        help="取得する最大件数（デフォルト: 5）"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="デバッグモードで詳細なログを表示"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🔍 特許検索機能テスト")
    print("=" * 60)
    print(f"キーワード: {args.keywords}")
    print(f"最大取得件数: {args.max_results}")
    print(f"デバッグモード: {'ON' if args.debug else 'OFF'}")
    print("-" * 60)
    print()
    
    try:
        # 特許検索を実行
        result = search_patents(
            keywords=args.keywords,
            max_results=args.max_results,
            debug=args.debug
        )
        
        print("=" * 60)
        print("📋 検索結果")
        print("=" * 60)
        print(result)
        print("=" * 60)
        
        # 結果の判定
        if "特許情報は見つかりませんでした" in result:
            print("\n⚠️  警告: 特許情報が見つかりませんでした")
            sys.exit(1)
        elif "特許検索エラー" in result:
            print("\n❌ エラー: 特許検索中にエラーが発生しました")
            sys.exit(1)
        else:
            print("\n✅ 成功: 特許情報を正常に取得しました")
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  ユーザーによって中断されました")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 予期しないエラーが発生しました: {str(e)}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

