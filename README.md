# Website Translation Tool

A standalone desktop application for extracting and translating website content into organized Excel files.

## Features

- **Website Scraping**: Extract content from any website via sitemap
- **Multi-language Translation**: Translate content using DeepL API  
- **Content Organization**: Organize content in document order with headings in bold
- **Excel Export**: Generate professional Excel files with translations
- **No API Key Required**: Works for content extraction without translation

## Quick Start

1. **Run the app:**
   ```bash
   python3 main.py
   ```

2. **For translation (requires DeepL API key):**
   - Get a free API key from https://www.deepl.com/pro-api
   - Enter your API key when prompted
   - Select target languages and click "Start Translation"

3. **For content extraction only (no API key needed):**
   - Choose "Continue without translation" when prompted
   - Click "Start Scraping"

## Building Distribution Package

```bash
python3 build_distribution.py
```

This creates a ready-to-share macOS application bundle.

## Output

Files are saved in `translation_outputs/`:
- **With translation**: `CompanyName.xlsx` (multiple language columns)
- **Content only**: `CompanyName_content_only.xlsx` (single language)

## Requirements

- Python 3.8+
- Required packages: `requests`, `beautifulsoup4`, `lxml`, `deepl`, `xlsxwriter`

## Installation

```bash
pip install -r requirements.txt
```

## Archive

The `archive_old_web_app/` directory contains the original Flask web application files for reference.
