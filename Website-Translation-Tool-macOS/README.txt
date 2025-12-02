# Website Translation Tool

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
