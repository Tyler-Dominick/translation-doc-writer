"""DeepL API key management"""

import os
from config import load_config, save_api_key


# Cached API key (module-level)
_CACHED_DEEPL_KEY = None


def prompt_deepl_key_gui():
    """Prompt user for API key via GUI and save it"""
    try:
        import tkinter as tk
        from tkinter import simpledialog
        root = tk.Tk()
        root.withdraw()
        key = simpledialog.askstring("DeepL API Key", "Enter your DeepL API key:", show='*')
        root.destroy()
        key = (key or "").strip()
        
        # Save key to config file if provided
        if key:
            save_api_key(key)
        
        return key
    except Exception:
        # Fallback to terminal prompt if GUI is unavailable
        try:
            import getpass
            key = getpass.getpass('Enter DeepL API key: ').strip()
            if key:
                save_api_key(key)
            return key
        except Exception:
            key = input('Enter DeepL API key: ').strip()
            if key:
                save_api_key(key)
            return key


def load_deepl_key():
    """Load API key from environment variable, config file, or prompt user"""
    # Check environment variable first
    env = os.getenv('DEEPL_API_KEY')
    if env:
        return env.strip()
    
    # Check config file
    config = load_config()
    if config.get('deepl_api_key'):
        return config['deepl_api_key'].strip()
    
    # If not found, prompt user
    return prompt_deepl_key_gui()


def get_deepl_key():
    """Get the DeepL API key (cached)"""
    global _CACHED_DEEPL_KEY
    if _CACHED_DEEPL_KEY is None:
        _CACHED_DEEPL_KEY = load_deepl_key()
    return _CACHED_DEEPL_KEY


def clear_cached_key():
    """Clear the cached API key (useful when key is changed)"""
    global _CACHED_DEEPL_KEY
    _CACHED_DEEPL_KEY = None

