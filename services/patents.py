"""
DuckDuckGoを使用した特許検索サービス
"""
import logging
from ddgs import DDGS
from typing import List, Dict, Union
import requests
from bs4 import BeautifulSoup

# ロガーの設定
logger = logging.getLogger(__name__)


def fetch_patent_abstract(patent_url: str, timeout: int = 10) -> str:
    """
    Google PatentsのURLから特許の要約を取得します。
    
    Args:
        patent_url: Google PatentsのURL
        timeout: リクエストのタイムアウト（秒）
    
    Returns:
        str: 特許の要約（取得できない場合は空文字列）
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(patent_url, headers=headers, timeout=timeout)
        
        if response.status_code != 200:
            logger.warning(f"特許URLの取得に失敗: {patent_url} (ステータスコード: {response.status_code})")
            return ""
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Google Patentsの要約を探す（複数のパターンを試す）
        abstract = None
        
        # パターン1: abstractクラスを持つdiv
        abstract = soup.find('div', {'class': 'abstract'})
        
        # パターン2: itemprop="description"を持つsection
        if not abstract:
            abstract = soup.find('section', {'itemprop': 'description'})
        
        # パターン3: abstractを含むクラス名
        if not abstract:
            abstract_elements = soup.find_all(['div', 'section'], class_=lambda x: x and 'abstract' in str(x).lower())
            if abstract_elements:
                abstract = abstract_elements[0]
        
        if abstract:
            # テキストを取得してクリーンアップ
            abstract_text = abstract.get_text(separator=' ', strip=True)
            # 余分な空白を削除
            abstract_text = ' '.join(abstract_text.split())
            return abstract_text
        else:
            logger.warning(f"要約が見つかりませんでした: {patent_url}")
            return ""
            
    except requests.exceptions.Timeout:
        logger.warning(f"特許URLの取得がタイムアウトしました: {patent_url}")
        return ""
    except requests.exceptions.RequestException as e:
        logger.warning(f"特許URLの取得エラー: {patent_url} - {str(e)}")
        return ""
    except Exception as e:
        logger.warning(f"要約取得エラー: {patent_url} - {str(e)}")
        return ""

def search_patents(keywords: Union[str, List[str]], max_results: int = 5, debug: bool = False) -> str:
    """
    DuckDuckGoを使用してGoogle Patents (site:patents.google.com) から特許を検索します。
    
    Args:
        keywords: 検索キーワード（文字列または文字列のリスト）
        max_results: 取得する最大件数
        debug: デバッグモード（詳細なログを出力）
        
    Returns:
        str: DuckDuckGoからの検索結果（テキスト）
    """
    try:
        # キーワードを文字列に変換（文字列の場合はそのまま、リストの場合は結合）
        if isinstance(keywords, str):
            query_str = keywords
        else:
            query_str = " ".join(keywords)
        
        # キーワードをクリーンアップ（余分なスペースを削除）
        query_str = " ".join(query_str.split())
        
        # 日本語文字が含まれているかチェック（ひらがな、カタカナ、漢字）
        import re
        has_japanese = bool(re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', query_str))
        
        # 括弧を含むキーワードの処理
        # 例：「(ライン幅ラフネス)」→「ライン幅ラフネス」、「EUV (極端紫外線)」→「EUV」
        def clean_keyword(kw):
            """キーワードから括弧とその中身を除去"""
            # 括弧で囲まれた部分を除去（例：「(ライン幅ラフネス)」→「」）
            kw = re.sub(r'\([^)]*\)', '', kw)
            # 括弧のみのキーワードを除去
            kw = kw.strip()
            # 空文字列の場合はNoneを返す
            return kw if kw else None
        
        # キーワードを分割して、括弧を除去
        keywords_list = []
        for kw in query_str.split():
            cleaned = clean_keyword(kw)
            if cleaned:
                keywords_list.append(cleaned)
        
        # キーワードリストが空の場合は元の文字列を使用
        if not keywords_list:
            keywords_list = query_str.split()
        keyword_count = len(keywords_list)
        
        # キーワードが多すぎる場合（15個以上）、主要なキーワードのみを使用
        # 英語略語（大文字のアルファベット）と重要な技術用語を優先
        MAX_KEYWORDS = 10  # 検索クエリに使用する最大キーワード数
        
        if keyword_count > MAX_KEYWORDS:
            # 技術用語のパターン定義
            # 重要な技術用語のパターン（材料、プロセス、用途など）
            technical_patterns = [
                r'.*樹脂$', r'.*材料$', r'.*成形$', r'.*プロセス$', r'.*方法$',
                r'.*接着剤$', r'.*複合材$', r'.*強化$', r'.*繊維$', r'.*電池$',
                r'.*電解質$', r'.*固体$', r'.*液体$', r'.*ガス$', r'.*膜$',
                r'.*コーティング$', r'.*処理$', r'.*製造$', r'.*合成$', r'.*分解$',
                r'.*反応$', r'.*触媒$', r'.*添加剤$', r'.*充填材$', r'.*改質$',
                r'.*硬化$', r'.*架橋$', r'.*重合$', r'.*共重合$', r'.*ブロック共重合$',
                r'.*グラフト共重合$', r'.*ランダム共重合$', r'.*交互共重合$',
                r'.*レジスト$', r'.*フォトレジスト$', r'.*リソグラフィ$',  # 半導体関連
                r'.*半導体$', r'.*プロセスノード$', r'.*微細加工$',  # 半導体製造
            ]
            
            # 一般的な形容詞的なキーワード（補助的に使用）
            # これらは優先度を下げるが、完全には除外しない
            auxiliary_patterns = [
                r'^高', r'^低', r'^優', r'^良', r'^強', r'^弱',
                r'^耐', r'^抗', r'^防', r'^速', r'^緩', r'^急',
                r'性$', r'度$', r'率$', r'比$', r'値$',  # 性質を表す接尾辞
            ]
            
            def calculate_keyword_priority(kw):
                """キーワードの優先度を計算（高いほど重要）"""
                priority = 0
                
                # 英語略語（最高優先度）
                if re.match(r'^[A-Z]{2,}$', kw):
                    return 1000 + len(kw)  # 長い略語ほど重要
                
                # 日本語キーワードの場合
                if has_japanese and re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', kw):
                    # 技術用語パターンに一致する場合（高優先度）
                    for pattern in technical_patterns:
                        if re.match(pattern, kw):
                            priority += 500
                            break
                    
                    # 複合語（長い単語）を優先
                    priority += len(kw) * 10
                    
                    # 漢字を含む複合語を優先（より専門的）
                    if re.search(r'[\u4E00-\u9FAF]', kw):
                        priority += 50
                    
                    # カタカナのみの単語は優先度を下げる（一般的な用語の可能性）
                    if re.match(r'^[\u30A0-\u30FF]+$', kw):
                        priority -= 20
                    
                    # 補助的な形容詞的なキーワードは優先度を下げる
                    for pattern in auxiliary_patterns:
                        if re.match(pattern, kw):
                            priority -= 100
                            break
                    
                    # 短すぎるキーワード（2文字以下）は優先度を下げる
                    if len(kw) <= 2:
                        priority -= 50
                
                # 英語キーワード（アルファベットと数字）
                elif re.match(r'^[A-Za-z0-9]+$', kw):
                    priority += 200 + len(kw) * 5
                
                return priority
            
            # キーワードを優先度でソート
            keywords_with_priority = [
                (kw, calculate_keyword_priority(kw))
                for kw in keywords_list
            ]
            keywords_with_priority.sort(key=lambda x: x[1], reverse=True)
            
            # 優先度の高いキーワードを選択
            priority_keywords = [kw for kw, _ in keywords_with_priority[:MAX_KEYWORDS]]
            
            optimized_query_str = " ".join(priority_keywords)
            
            if debug:
                print(f"[DEBUG] キーワード数が多すぎるため最適化: {keyword_count}個 → {len(priority_keywords)}個")
                print(f"[DEBUG] キーワード優先度ランキング（上位{min(MAX_KEYWORDS, len(keywords_with_priority))}個）:")
                for i, (kw, priority) in enumerate(keywords_with_priority[:MAX_KEYWORDS], 1):
                    print(f"[DEBUG]   {i}. {kw} (優先度: {priority})")
                print(f"[DEBUG] 最適化後のキーワード: {optimized_query_str}")
        else:
            optimized_query_str = query_str
        
        # 検索クエリのリストを構築
        # 日本語キーワードと英語キーワードが混在している場合、
        # 複数の検索クエリを試すことで検索精度を向上させる
        queries = []
        seen_queries = set()  # 重複を避けるため
        
        def add_query_if_unique(query):
            """重複しないクエリのみを追加"""
            if query and query not in seen_queries:
                seen_queries.add(query)
                queries.append(query)
        
        if has_japanese:
            # 日本語キーワードがある場合
            # 1. 英語略語のみのクエリ（短く、具体的）- 最優先
            english_only = " ".join([w for w in optimized_query_str.split() if re.match(r'^[A-Za-z0-9]+$', w)])
            if english_only:
                add_query_if_unique(f"{english_only} 特許")
            
            # 2. 主要な技術用語のみ（日本語の名詞を抽出、3-5個に制限）
            # 「特許」というキーワード自体は除外（検索クエリに追加するため）
            japanese_words = [
                w for w in optimized_query_str.split()
                if re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', w) and w != "特許"
            ]
            
            if japanese_words:
                # 括弧を含むキーワードから括弧を除去
                japanese_words = [clean_keyword(w) for w in japanese_words if clean_keyword(w)]
                # 3-5個のキーワードに制限（長すぎるクエリを避ける）
                if len(japanese_words) > 5:
                    # 長い単語を優先（より具体的な技術用語）
                    japanese_words_sorted = sorted(japanese_words, key=len, reverse=True)
                    japanese_only = " ".join(japanese_words_sorted[:5])
                else:
                    japanese_only = " ".join(japanese_words)
                if japanese_only:
                    add_query_if_unique(f"{japanese_only} 特許")
            
            # 3. 英語略語 + 主要な日本語キーワード（2-3個）の組み合わせ
            if english_only and japanese_words:
                if len(japanese_words) >= 2:
                    # 最初の2-3個の日本語キーワードを使用
                    short_japanese = " ".join(japanese_words[:3])
                    combined_query = f"{english_only} {short_japanese} 特許"
                    # クエリ1やクエリ2と重複しない場合のみ追加
                    if combined_query != f"{english_only} 特許" and combined_query != f"{japanese_only} 特許":
                        add_query_if_unique(combined_query)
            
            # 4. 最適化されたキーワード全体（括弧を除去してから使用、「特許」を除外）
            optimized_words = [
                clean_keyword(w) for w in optimized_query_str.split()
                if clean_keyword(w) and clean_keyword(w) != "特許"
            ]
            optimized_cleaned = " ".join(optimized_words)
            if optimized_cleaned and len(optimized_cleaned.split()) <= 8:  # 8個以下に制限
                final_query = f"{optimized_cleaned} 特許"
                # 既存のクエリと重複しない場合のみ追加
                if final_query not in seen_queries:
                    add_query_if_unique(final_query)
        else:
            # 英語キーワードのみの場合
            add_query_if_unique(f"{optimized_query_str} patent")
            add_query_if_unique(f"{optimized_query_str} patent 2024 2025")
        
        logger.info(f"🔍 特許検索開始: キーワード={optimized_query_str}, 検索クエリ数={len(queries)}, max_results={max_results}")
        if debug:
            print(f"[DEBUG] 🔍 特許検索開始")
            print(f"[DEBUG] 元のキーワード: {query_str}")
            print(f"[DEBUG] 最適化後のキーワード: {optimized_query_str}")
            print(f"[DEBUG] キーワード数: {keyword_count}個")
            print(f"[DEBUG] 日本語キーワード検出: {has_japanese}")
            print(f"[DEBUG] 検索クエリ数: {len(queries)}")
            for i, q in enumerate(queries, 1):
                print(f"[DEBUG]  クエリ {i}: {q}")
            print(f"[DEBUG] 最大取得件数: {max_results}")
        
        results_list = []
        result_count = 0
        seen_urls = set()  # 重複を避けるため
        
        with DDGS() as ddgs:
            # 各クエリを順番に試す
            for query_idx, query in enumerate(queries, 1):
                if result_count >= max_results:
                    break
                
                if debug:
                    print(f"[DEBUG] クエリ {query_idx}/{len(queries)} を実行中...")
                
                # 日本語キーワードの場合は特許サイトの結果が少ない可能性があるため、
                # より多くの結果を取得してフィルタリング（max_results * 5）
                # 英語キーワードの場合は max_results * 3 で十分
                fetch_limit = max_results * 5 if has_japanese else max_results * 3
                
                try:
                    total_fetched = 0
                    patents_found = 0
                    all_urls = []  # デバッグ用：取得したURLのリスト
                    
                    # DuckDuckGoの検索を実行
                    search_results = ddgs.text(query, max_results=fetch_limit)
                    
                    for r in search_results:
                        total_fetched += 1
                        href = r.get("href", "")
                        title = r.get("title", "")
                        all_urls.append(href)
                        
                        if debug and total_fetched <= 3:
                            print(f"[DEBUG]   取得結果 #{total_fetched}: {title[:60]}...")
                            print(f"[DEBUG]      URL: {href}")
                        
                        # patents.google.comのURLのみをフィルタリングし、重複を避ける
                        if "patents.google.com" in href and href not in seen_urls:
                            seen_urls.add(href)
                            patents_found += 1
                            result_count += 1
                            
                            # Google Patentsから要約を取得
                            if debug:
                                print(f"[DEBUG] 検索結果 #{result_count} (クエリ{query_idx}, 総取得: {total_fetched}件):")
                                print(f"[DEBUG]  タイトル: {r['title']}")
                                print(f"[DEBUG]  URL: {href}")
                                print(f"[DEBUG]  スニペット: {r['body'][:100]}...")
                                print(f"[DEBUG]  Google Patentsから要約を取得中...")
                            
                            abstract = fetch_patent_abstract(href)
                            
                            # 結果テキストを構築（要約があれば含める）
                            result_text = f"Title: {r['title']}\nURL: {href}\n"
                            if abstract:
                                result_text += f"Abstract: {abstract}\n"
                            else:
                                # 要約が取得できない場合はスニペットを使用
                                result_text += f"Snippet: {r['body']}\n"
                            
                            results_list.append(result_text)
                            
                            if debug:
                                if abstract:
                                    print(f"[DEBUG]  要約: {abstract[:200]}...")
                                else:
                                    print(f"[DEBUG]  要約: 取得できませんでした（スニペットを使用）")
                            
                            # 必要な件数に達したら終了
                            if result_count >= max_results:
                                break
                    
                    if debug:
                        print(f"[DEBUG] クエリ {query_idx}: 総取得件数={total_fetched}件, 特許サイトの結果={patents_found}件")
                        if total_fetched == 0:
                            print(f"[DEBUG] ⚠️ 警告: 検索結果が0件です。DuckDuckGoの検索APIが利用できない可能性があります。")
                        elif patents_found == 0 and total_fetched > 0:
                            print(f"[DEBUG] ⚠️ 警告: 検索結果は{total_fetched}件ありましたが、特許サイトの結果が0件です。")
                            if total_fetched <= 5:
                                print(f"[DEBUG]   取得したURLの例: {all_urls[:3]}")
                        
                except Exception as e:
                    if debug:
                        print(f"[DEBUG] クエリ {query_idx} でエラー: {type(e).__name__}: {str(e)}")
                        import traceback
                        traceback.print_exc()
                    continue
            
            if debug:
                print(f"[DEBUG] 最終結果: {result_count}件の特許を取得")
        
        if not results_list:
            logger.warning(f"⚠️ 特許情報が見つかりませんでした: クエリ={query}")
            if debug:
                print(f"[DEBUG] ⚠️ 特許情報が見つかりませんでした")
            return "特許情報は見つかりませんでした。"
        
        logger.info(f"✅ 特許検索完了: {result_count}件の結果を取得")
        if debug:
            print(f"[DEBUG] ✅ 特許検索完了: {result_count}件の結果を取得")
            
        return "\n".join(results_list)
    except Exception as e:
        error_msg = f"特許検索エラー: {str(e)}"
        logger.error(f"❌ {error_msg}", exc_info=True)
        if debug:
            print(f"[DEBUG] ❌ エラー発生: {str(e)}")
            import traceback
            traceback.print_exc()
        return error_msg
