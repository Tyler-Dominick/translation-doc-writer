"""Configuration file management"""

import os
import json
from pathlib import Path


def get_config_path():
    """Get the path to the config file"""
    config_dir = Path.home() / ".website-translation-tool"
    config_dir.mkdir(exist_ok=True)
    return config_dir / "config.json"


def load_config():
    """Load config from JSON file"""
    config_path = get_config_path()
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_config(config_dict):
    """Save config to JSON file"""
    config_path = get_config_path()
    try:
        with open(config_path, 'w') as f:
            json.dump(config_dict, f, indent=2)
        # Set file permissions to be readable only by user (Unix/macOS)
        try:
            os.chmod(config_path, 0o600)
        except (OSError, AttributeError):
            pass  # Windows doesn't support chmod the same way
        return True
    except (IOError, OSError):
        return False


def save_api_key(key):
    """Save API key to config file"""
    config = load_config()
    config['deepl_api_key'] = key
    return save_config(config)

