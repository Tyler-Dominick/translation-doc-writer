"""Update checking functionality"""

import threading
import requests
import webbrowser
from tkinter import messagebox
from constants import VERSION, GITHUB_REPO_OWNER, GITHUB_REPO_NAME, GITHUB_RELEASES_URL


def compare_versions(current, latest):
    """Compare version strings (simple numeric comparison)"""
    def version_tuple(v):
        # Remove 'v' prefix if present and split by dots
        v = v.lstrip('vV')
        parts = []
        for part in v.split('.'):
            try:
                parts.append(int(part))
            except ValueError:
                # Handle non-numeric parts (e.g., "1.0.0-beta")
                parts.append(0)
        return tuple(parts)
    
    try:
        current_tuple = version_tuple(current)
        latest_tuple = version_tuple(latest)
        return latest_tuple > current_tuple
    except Exception:
        # If comparison fails, assume no update needed
        return False


def check_for_updates(callback=None):
    """Check for updates from GitHub Releases API (non-blocking)"""
    def check():
        try:
            api_url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases/latest"
            response = requests.get(api_url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                latest_version = data.get('tag_name', '').lstrip('vV')
                
                if latest_version and compare_versions(VERSION, latest_version):
                    # Update available
                    if callback:
                        callback(latest_version, data.get('html_url', GITHUB_RELEASES_URL))
        except Exception:
            # Silently fail - don't interrupt user experience
            pass
    
    # Run in background thread
    thread = threading.Thread(target=check, daemon=True)
    thread.start()


def show_update_dialog(root, latest_version, download_url):
    """Show update notification dialog"""
    def open_download():
        webbrowser.open(download_url)
    
    message = (
        f"A new version is available!\n\n"
        f"Current version: {VERSION}\n"
        f"Latest version: {latest_version}\n\n"
        f"Would you like to download the update?"
    )
    
    result = messagebox.askyesno("Update Available", message)
    if result:
        open_download()

