"""
Google翻訳を使用した翻訳サービス
"""
from googletrans import Translator
from typing import Optional

def translate_to_japanese(text: str, source_lang: str = 'auto') -> Optional[str]:
    """
    テキストを日本語に翻訳します。
    
    Args:
        text: 翻訳するテキスト
        source_lang: ソース言語（デフォルトは自動検出）
        
    Returns:
        Optional[str]: 翻訳されたテキスト、エラーの場合はNone
    """
    try:
        translator = Translator()
        result = translator.translate(text, src=source_lang, dest='ja')
        return result.text
    except Exception as e:
        print(f"翻訳エラー: {e}")
        return None

def translate_text(text: str, dest_lang: str = 'ja', source_lang: str = 'auto') -> Optional[str]:
    """
    テキストを指定された言語に翻訳します。
    
    Args:
        text: 翻訳するテキスト
        dest_lang: 翻訳先の言語コード（デフォルトは日本語）
        source_lang: ソース言語（デフォルトは自動検出）
        
    Returns:
        Optional[str]: 翻訳されたテキスト、エラーの場合はNone
    """
    try:
        translator = Translator()
        result = translator.translate(text, src=source_lang, dest=dest_lang)
        return result.text
    except Exception as e:
        print(f"翻訳エラー: {e}")
        return None
