#!/usr/bin/env python3
"""
Build script to create a distribution package for the Website Translation Tool
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

def clean_build():
    """Clean previous build artifacts"""
    print("🧹 Cleaning previous builds...")
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"   Removed {dir_name}/")

def build_executable():
    """Build the standalone executable"""
    print("🔨 Building executable...")
    
    # PyInstaller command for macOS
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',
        '--windowed',
        '--name=Website-Translation-Tool',
        '--hidden-import=tkinter',
        '--hidden-import=tkinter.ttk',
        '--hidden-import=tkinter.messagebox',
        '--hidden-import=tkinter.simpledialog',
        '--hidden-import=bs4',
        '--hidden-import=lxml',
        '--hidden-import=deepl',
        '--hidden-import=xlsxwriter',
        '--hidden-import=requests',
        '--hidden-import=pathlib',
        'main.py'
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("   ✅ Executable built successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Build failed: {e}")
        return False

def create_distribution_package():
    """Create the final distribution package"""
    print("📦 Creating distribution package...")
    
    # Create distribution directory
    dist_dir = Path("Website-Translation-Tool-Distribution")
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir()
    
    # Copy executable
    app_path = Path("dist/Website-Translation-Tool.app")
    if app_path.exists():
        shutil.copytree(app_path, dist_dir / "Website-Translation-Tool.app")
        print("   ✅ Copied .app bundle")
    else:
        print("   ❌ .app bundle not found")
        return False
    
    # Create README
    readme_content = """# Website Translation Tool

A powerful tool for extracting and translating website content into organized Excel files.

## Features

- **Website Scraping**: Extract content from any website via sitemap
- **Multi-language Translation**: Translate content using DeepL API
- **Content Organization**: Organize content in document order with headings in bold
- **Excel Export**: Generate professional Excel files with translations
- **No API Key Required**: Works for content extraction without translation

## How to Use

### Option 1: With Translation (Requires DeepL API Key)
1. Get a free DeepL API key from https://www.deepl.com/pro-api
2. Run the app and enter your API key when prompted
3. Enter website URL and click "Fetch URLs"
4. Select URLs to translate
5. Choose source and target languages
6. Click "Start Translation"

### Option 2: Content Extraction Only (No API Key Needed)
1. Run the app and choose "Continue without translation" when prompted
2. Enter website URL and click "Fetch URLs"
3. Select URLs to extract
4. Click "Start Scraping"

## Output

- Files are saved in: `~/Documents/Website-Translation-Tool-Outputs/`
- Translated content: `CompanyName.xlsx`
- Content only: `CompanyName_content_only.xlsx`

## System Requirements

- macOS 10.14 or later
- No additional software required

## Troubleshooting

- If the app won't open, right-click and select "Open"
- For websites without sitemaps, the tool will show an error
- Make sure the website URL includes http:// or https://
- If you get permission errors, the app will automatically use a temp directory

## Support

For issues or questions, please contact the developer.
"""
    
    with open(dist_dir / "README.txt", "w") as f:
        f.write(readme_content)
    
    # Create a simple launcher script
    launcher_content = """#!/bin/bash
# Website Translation Tool Launcher
echo "Starting Website Translation Tool..."
echo "Output files will be saved to: ~/Documents/Website-Translation-Tool-Outputs/"
open "Website-Translation-Tool.app"
"""
    
    with open(dist_dir / "Launch-Tool.command", "w") as f:
        f.write(launcher_content)
    
    # Make launcher executable
    os.chmod(dist_dir / "Launch-Tool.command", 0o755)
    
    print("   ✅ Created README and launcher")
    
    # Create zip file
    print("📦 Creating zip file...")
    shutil.make_archive("Website-Translation-Tool-macOS", "zip", dist_dir)
    print("   ✅ Created Website-Translation-Tool-macOS.zip")
    
    return True

def main():
    """Main build process"""
    print("🚀 Building Website Translation Tool Distribution Package")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("main.py"):
        print("❌ Error: main.py not found. Run this script from the project directory.")
        sys.exit(1)
    
    # Clean previous builds
    clean_build()
    
    # Build executable
    if not build_executable():
        print("❌ Build failed. Exiting.")
        sys.exit(1)
    
    # Create distribution package
    if create_distribution_package():
        print("\n🎉 Distribution package created successfully!")
        print("\nFiles created:")
        print("  📁 Website-Translation-Tool-Distribution/")
        print("  📦 Website-Translation-Tool-macOS.zip")
        print("\nReady to share! 🚀")
        print("\nNote: Output files will be saved to ~/Documents/Website-Translation-Tool-Outputs/")
    else:
        print("❌ Failed to create distribution package.")
        sys.exit(1)

if __name__ == "__main__":
    main()
