"""Translation functionality with caching"""

import deepl
from api_key import get_deepl_key


# Translation cache (in-memory, session-only)
_translation_cache = {}

# DeepL translator instance
_translator = None


def get_translator():
    """Get or create the DeepL translator instance"""
    global _translator
    if _translator is None:
        _translator = deepl.Translator(get_deepl_key())
    return _translator


def translate_text(text, target_language):
    """Translate text using DeepL API with caching"""
    # Create cache key with target language to handle multiple target languages
    cache_key = f"{target_language}|{text}"
    
    # Check cache first
    if cache_key in _translation_cache:
        return _translation_cache[cache_key]
    
    # If not in cache, translate and store
    translation = get_translator().translate_text(text, target_lang=target_language)
    translated_text = translation.text
    _translation_cache[cache_key] = translated_text
    return translated_text


def clear_translator():
    """Clear the translator instance (useful when API key changes)"""
    global _translator
    _translator = None

