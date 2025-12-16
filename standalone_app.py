import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import requests
from bs4 import BeautifulSoup
import xlsxwriter
import deepl

# API Key management
_CACHED_DEEPL_KEY = None

# Translation cache (in-memory, session-only)
_translation_cache = {}

def _prompt_deepl_key_gui():
    try:
        import tkinter as tk
        from tkinter import simpledialog
        root = tk.Tk()
        root.withdraw()
        key = simpledialog.askstring("DeepL API Key", "Enter your DeepL API key:", show='*')
        root.destroy()
        return (key or "").strip()
    except Exception:
        # Fallback to terminal prompt if GUI is unavailable
        try:
            import getpass
            return getpass.getpass('Enter DeepL API key: ').strip()
        except Exception:
            return input('Enter DeepL API key: ').strip()

def _load_deepl_key():
    env = os.getenv('DEEPL_API_KEY')
    if env:
        return env.strip()
    return _prompt_deepl_key_gui()

def get_deepl_key():
    global _CACHED_DEEPL_KEY
    if _CACHED_DEEPL_KEY is None:
        _CACHED_DEEPL_KEY = _load_deepl_key()
    return _CACHED_DEEPL_KEY

# URL fetching function
def get_all_urls(base_url, blogs):
    """Fetch all URLs from website sitemap"""
    resp = requests.get(base_url + 'sitemap.xml')
    soup = BeautifulSoup(resp.content, 'xml')
    site_maps = soup.findAll('sitemap')
    
    out = set()
    print(f'{blogs}')
    for site_map in site_maps:
        map = site_map.find('loc').string
        if map == (base_url + "post-sitemap.xml") and (blogs=='no'):
            continue
        else:
            response = requests.get(map)
            sitemap_soup = BeautifulSoup(response.content, 'xml')
            urls = sitemap_soup.findAll('url')
            for u in urls:
                loc = u.find('loc').string
                out.add(loc)
    return out

# Translation functions
_translator = None

def _get_translator():
    global _translator
    if _translator is None:
        _translator = deepl.Translator(get_deepl_key())
    return _translator

def translate_text(text, target_language):
    # Create cache key with target language to handle multiple target languages
    cache_key = f"{target_language}|{text}"
    
    # Check cache first
    if cache_key in _translation_cache:
        return _translation_cache[cache_key]
    
    # If not in cache, translate and store
    translation = _get_translator().translate_text(text, target_lang=target_language)
    translated_text = translation.text
    _translation_cache[cache_key] = translated_text
    return translated_text

def fetch_and_parse(url):
    response = requests.get(url)
    html_content = response.text
    soup = BeautifulSoup(html_content, 'lxml')
    return soup

def write_content(worksheet, start_row, col, content, translate=False, target_language=None):
    row = start_row
    if isinstance(content, str):
        worksheet.write(row, col, content)
        if translate:
            translated_text = translate_text(content, target_language)
            worksheet.write(row, col, translated_text)
            row += 1
        return start_row, row
    else:
        for item in content:
            text = item.get_text().strip()
            if text:
                worksheet.write(row, col, text)
                if translate:
                    translated_text = translate_text(text, target_language)
                    worksheet.write(row, col, translated_text)
                row += 1
        return start_row, row

def create_translation_doc(company_name, all_urls, source_language, target_languages, progress_callback=None):
    """Create translation document with DeepL translations"""
    workbook = xlsxwriter.Workbook(f'{company_name}.xlsx')
    bold = workbook.add_format({'bold': True})
    
    total_urls = len(all_urls)
    current_progress = 10  # Start at 10% after initialization

    worksheet = workbook.add_worksheet("Table of Contents")
    row, col = 0, 0
    sheet_counter = 2

    # Table of contents
    if progress_callback:
        progress_callback(current_progress, "Creating table of contents...", "", "Organizing URLs...")
    
    for url in all_urls:
        worksheet.write(row, col, url.address)
        worksheet.write(row, col + 1, f"Sheet {sheet_counter}")
        sheet_counter += 1
        row += 1

    # Process each URL
    for i, url in enumerate(all_urls):
        url_progress = 10 + (i * 80) // total_urls  # 10% to 90%
        
        if progress_callback:
            progress_callback(url_progress, f"Processing URLs ({i+1} of {total_urls})", url.address, "Fetching page...")
        
        print(f'Working on: {url.address}')
        soup = fetch_and_parse(url.address)
        
        if progress_callback:
            progress_callback(url_progress + 2, f"Processing URLs ({i+1} of {total_urls})", url.address, "Parsing content...")
        worksheet = workbook.add_worksheet()

        # Add source language and target languages to the worksheet
        worksheet.write('A1', url.address)
        worksheet.write('A2', source_language)
        for idx, target_language in enumerate(target_languages):
            worksheet.write(1, idx + 1, target_language)

        # Extract content from the main section of the HTML
        site_content = soup.find('main')
        title = soup.find('title')
        meta = soup.find('meta', attrs={'name':'description'})
        try:
            meta_desc = meta['content']
        except Exception as e:
            meta_desc = "None"
            print(f"Error: {e}")

        headings = site_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']) if site_content else []
        paragraphs = site_content.find_all('p') if site_content else []
        lists = site_content.find_all('li') if site_content else []
        # Gather elements in the same order as they appear on the page
        ordered_elements = site_content.find_all(
            ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li']
        ) if site_content else []

        #write title
        if progress_callback:
            progress_callback(url_progress + 4, f"Processing URLs ({i+1} of {total_urls})", url.address, "Writing content to Excel...")
        
        row = 3
        worksheet.write(row, 0, 'Title Tag:', bold)
        start_row = row + 1
        _, row = write_content(worksheet, start_row, 0, title, False)
        for idx, target_language in enumerate(target_languages):
            if target_language == source_language:
                continue
            write_content(worksheet, start_row, idx + 1, title, True, target_language)

        #write Meta Desc
        row +=2
        worksheet.write(row, 0, 'Meta Description', bold)
        start_row = row + 1
        _, row = write_content(worksheet, start_row, 0, meta_desc, False)
        for idx, target_language in enumerate(target_languages):
            if target_language == source_language:
                continue
            write_content(worksheet, start_row, idx + 1, meta_desc, True, target_language)

        # Write content in document order (headings, paragraphs, list items)
        row += 2
        worksheet.write(row, 0, 'Content (ordered):', bold)
        start_row = row + 1
        row = start_row
        for element in ordered_elements:
            try:
                text = element.get_text().strip()
            except Exception:
                text = ""
            if not text:
                continue
            is_heading = hasattr(element, 'name') and element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
            # Write source text with formatting if heading
            if is_heading:
                worksheet.write(row, 0, text, bold)
            else:
                worksheet.write(row, 0, text)
            # Write translations in same row with matching formatting
            for idx, target_language in enumerate(target_languages):
                if target_language == source_language:
                    continue
                translated_text = translate_text(text, target_language)
                if is_heading:
                    worksheet.write(row, idx + 1, translated_text, bold)
                else:
                    worksheet.write(row, idx + 1, translated_text)
            row += 1

    if progress_callback:
        progress_callback(95, "Finalizing document...", "", "Saving Excel file...")
    
    workbook.close()
    print("Translation document created successfully!")
    
    if progress_callback:
        progress_callback(100, "Translation complete!", "", "")
    
    return workbook

class TranslationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Website Translation Tool")
        self.root.geometry("900x700")
        
        # Variables
        self.base_url = tk.StringVar()
        self.company_name = tk.StringVar()
        self.source_language = tk.StringVar(value="EN-US - English (US)")
        self.target_languages = []
        self.include_blogs = tk.BooleanVar(value=False)
        self.selected_urls = []
        self.all_urls = []
        self.has_api_key = False
        
        self.setup_ui()
        self.check_api_key_status()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Step 1: URL Input
        ttk.Label(main_frame, text="Step 1: Enter Website URL", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        ttk.Label(main_frame, text="Base URL:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        url_entry = ttk.Entry(main_frame, textvariable=self.base_url, width=50)
        url_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Checkbutton(main_frame, text="Include blog posts", variable=self.include_blogs).grid(row=2, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Button(main_frame, text="Fetch URLs", command=self.fetch_urls).grid(row=3, column=1, sticky=tk.W, pady=(0, 20))
        
        # Step 2: URL Selection
        ttk.Label(main_frame, text="Step 2: Select URLs to Translate", font=("Arial", 12, "bold")).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # URL listbox with scrollbar
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        self.url_listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE, height=12)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.url_listbox.yview)
        self.url_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.url_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # URL selection buttons
        url_button_frame = ttk.Frame(main_frame)
        url_button_frame.grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        ttk.Button(url_button_frame, text="Select All", command=self.select_all_urls).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(url_button_frame, text="Select None", command=self.select_none_urls).grid(row=0, column=1, padx=(0, 5))
        ttk.Label(url_button_frame, text="(Hold Ctrl/Cmd to select multiple individually)", font=("Arial", 8)).grid(row=0, column=2, padx=(10, 0))
        
        # Step 3: Document Settings
        ttk.Label(main_frame, text="Step 3: Document Settings", font=("Arial", 12, "bold")).grid(row=7, column=0, columnspan=2, sticky=tk.W, pady=(20, 10))
        
        doc_settings_frame = ttk.Frame(main_frame)
        doc_settings_frame.grid(row=8, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        doc_settings_frame.columnconfigure(1, weight=1)
        
        ttk.Label(doc_settings_frame, text="Company Name:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        ttk.Entry(doc_settings_frame, textvariable=self.company_name, width=30).grid(row=0, column=1, sticky=tk.W, pady=(0, 5))
        
        # Step 4: Language Settings (only if API key available)
        self.language_frame = ttk.LabelFrame(main_frame, text="Language Settings (Translation Mode)")
        self.language_frame.grid(row=9, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 10))
        self.language_frame.columnconfigure(1, weight=1)
        
        ttk.Label(self.language_frame, text="Source Language:").grid(row=0, column=0, sticky=tk.W, padx=(10, 10), pady=(10, 5))
        self.source_combo = ttk.Combobox(self.language_frame, textvariable=self.source_language, width=20)
        
        # Language code to English name mapping (reused for source language)
        language_names = {
            'AR': 'Arabic',
            'BG': 'Bulgarian',
            'CS': 'Czech',
            'ZH-HANS': 'Chinese (Simplified)',
            'ZH-HANT': 'Chinese (Traditional)',
            'DA': 'Danish',
            'NL': 'Dutch',
            'EN-GB': 'English (UK)',
            'EN-US': 'English (US)',
            'ET': 'Estonian',
            'FI': 'Finnish',
            'FR': 'French',
            'DE': 'German',
            'EL': 'Greek',
            'HU': 'Hungarian',
            'ID': 'Indonesian',
            'IT': 'Italian',
            'JA': 'Japanese',
            'KO': 'Korean',
            'LT': 'Lithuanian',
            'LV': 'Latvian',
            'NB': 'Norwegian (Bokmål)',
            'PL': 'Polish',
            'PT-PT': 'Portuguese (Portugal)',
            'PT-BR': 'Portuguese (Brazil)',
            'RO': 'Romanian',
            'RU': 'Russian',
            'SK': 'Slovak',
            'SL': 'Slovenian',
            'ES': 'Spanish',
            'SV': 'Swedish',
            'TH': 'Thai',
            'TR': 'Turkish',
            'UK': 'Ukrainian',
            'VI': 'Vietnamese',
        }
        
        # Create display values for source language dropdown (using all available languages)
        source_languages = list(language_names.keys())
        source_languages.sort()  # Sort alphabetically for better UX
        source_display_values = [f"{lang} - {language_names[lang]}" for lang in source_languages]
        self.source_combo['values'] = source_display_values
        self.source_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 10), pady=(10, 5))
        
        ttk.Label(self.language_frame, text="Target Languages:").grid(row=1, column=0, sticky=tk.W, padx=(10, 10), pady=(5, 10))
        self.target_frame = ttk.Frame(self.language_frame)
        self.target_frame.grid(row=1, column=1, sticky=tk.W, padx=(0, 10), pady=(5, 10))
        
        # Target language checkboxes (using all available languages)
        self.target_vars = {}
        languages = list(language_names.keys())
        languages.sort()  # Sort alphabetically for better UX
        
        for i, lang in enumerate(languages):
            var = tk.BooleanVar()
            var.trace('w', self.on_target_language_change)
            self.target_vars[lang] = var
            # Display both code and English name
            display_text = f"{lang} ({language_names[lang]})"
            cb = ttk.Checkbutton(self.target_frame, text=display_text, variable=var)
            cb.grid(row=i//5, column=i%5, sticky=tk.W, padx=(0, 10))
        
        # Step 5: Progress and Start
        self.step_label = ttk.Label(main_frame, text="Step 5: Start Processing", font=("Arial", 12, "bold"))
        self.step_label.grid(row=10, column=0, columnspan=2, sticky=tk.W, pady=(20, 10))
        
        # Progress section with multiple levels
        self.progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding=10)
        self.progress_frame.grid(row=11, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Overall progress bar
        self.progress = ttk.Progressbar(self.progress_frame, mode='determinate')
        self.progress.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Progress percentage label
        self.progress_percent = ttk.Label(self.progress_frame, text="0%")
        self.progress_percent.grid(row=0, column=2, padx=(5, 0))
        
        # Status line 1: Current step
        self.status_label = ttk.Label(self.progress_frame, text="Ready to start")
        self.status_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(5, 2))
        
        # Status line 2: Current URL being processed
        self.current_url_label = ttk.Label(self.progress_frame, text="", foreground="gray")
        self.current_url_label.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=(0, 2))
        
        # Status line 3: Current operation
        self.current_operation_label = ttk.Label(self.progress_frame, text="", foreground="green")
        self.current_operation_label.grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=(0, 0))
        
        # Button frame for Start and New buttons
        self.button_frame = ttk.Frame(main_frame)
        self.button_frame.grid(row=12, column=0, columnspan=2, pady=(0, 10))
        
        self.start_button = ttk.Button(self.button_frame, text="Start Scraping", command=self.start_translation)
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        self.new_button = ttk.Button(self.button_frame, text="New Scraping", command=self.reset_form)
        self.new_button.grid(row=0, column=1)
        
        # Configure main frame grid weights
        main_frame.rowconfigure(5, weight=1)
    
    def check_api_key_status(self):
        """Check if API key is available and update UI accordingly"""
        try:
            api_key = get_deepl_key()
            self.has_api_key = bool(api_key)
        except:
            self.has_api_key = False
        
        self.update_ui_for_mode()
    
    def update_ui_for_mode(self):
        """Update UI based on whether API key is available"""
        if self.has_api_key:
            # Translation mode - enable language settings
            self.language_frame.config(text="Language Settings (Translation Mode)")
            self.source_combo.config(state='readonly')
            for cb in self.target_frame.winfo_children():
                if isinstance(cb, ttk.Checkbutton):
                    cb.config(state='normal')
            
            # Check if target languages are selected
            target_langs = [lang for lang, var in self.target_vars.items() if var.get()]
            if target_langs:
                self.start_button.config(text="Start Translation")
                self.new_button.config(text="New Translation")
                self.step_label.config(text="Step 5: Start Translation")
            else:
                self.start_button.config(text="Start Scraping")
                self.new_button.config(text="New Scraping")
                self.step_label.config(text="Step 5: Start Scraping")
        else:
            # Scraping mode - disable language settings
            self.language_frame.config(text="Language Settings (Scraping Mode - Disabled)")
            self.source_combo.config(state='disabled')
            for cb in self.target_frame.winfo_children():
                if isinstance(cb, ttk.Checkbutton):
                    cb.config(state='disabled')
            
            self.start_button.config(text="Start Scraping")
            self.new_button.config(text="New Scraping")
            self.step_label.config(text="Step 5: Start Scraping")
    
    def on_target_language_change(self, *args):
        """Called when target language selection changes"""
        if self.has_api_key:
            self.update_ui_for_mode()
        
    def fetch_urls(self):
        """Fetch URLs from the website sitemap"""
        if not self.base_url.get().strip():
            messagebox.showerror("Error", "Please enter a base URL")
            return
            
        self.update_progress(0, "Fetching URLs...", "", "Connecting to sitemap...")
        
        def fetch_thread():
            try:
                # Ensure URL ends with /
                url = self.base_url.get().strip()
                if not url.endswith('/'):
                    url += '/'
                
                self.all_urls = list(get_all_urls(url, 'yes' if self.include_blogs.get() else 'no'))
                
                # Update UI in main thread
                self.root.after(0, self.update_url_list)
                
            except Exception as e:
                error_msg = f"Error fetching URLs: {str(e)}"
                self.root.after(0, lambda: self.show_error(error_msg))
        
        threading.Thread(target=fetch_thread, daemon=True).start()
    
    def update_url_list(self):
        """Update the URL listbox with fetched URLs"""
        self.url_listbox.delete(0, tk.END)
        for i, url in enumerate(self.all_urls):
            self.url_listbox.insert(tk.END, f"{i+1}. {url}")
        
        self.update_progress(100, f"Found {len(self.all_urls)} URLs", "", "")
        self.clear_progress_details()
    
    def start_translation(self):
        """Start the translation process"""
        # Validate inputs
        if not self.company_name.get().strip():
            messagebox.showerror("Error", "Please enter a company name")
            return
            
        if not self.base_url.get().strip():
            messagebox.showerror("Error", "Please enter a base URL")
            return
            
        # Get selected URLs
        selected_indices = self.url_listbox.curselection()
        if not selected_indices:
            messagebox.showerror("Error", "Please select at least one URL to process")
            return
            
        # Get target languages (optional - if none selected, will do content scraping only)
        target_langs = [lang for lang, var in self.target_vars.items() if var.get()]
            
        # Get selected URLs
        selected_urls = [self.all_urls[i] for i in selected_indices]
        
        # Start translation in background thread
        self.update_progress(0, "Starting translation...", "", "Initializing...")
        
        def translation_thread():
            try:
                # Create URL objects (simplified for standalone app)
                class SimpleURL:
                    def __init__(self, address):
                        self.address = address
                
                url_objects = [SimpleURL(url) for url in selected_urls]
                
                # Update status to show we're starting
                self.update_progress(5, "Starting translation...", "", "Preparing output directory...")
                
                # Create output directory in user's Documents folder
                import os.path
                home_dir = os.path.expanduser("~")
                output_dir = os.path.join(home_dir, "Documents", "Website-Translation-Tool-Outputs")
                
                # Try to create the directory, with fallbacks
                try:
                    if not os.path.exists(output_dir):
                        os.makedirs(output_dir)
                except (OSError, PermissionError):
                    # Fallback to current directory if Documents folder is not accessible
                    output_dir = "translation_outputs"
                    if not os.path.exists(output_dir):
                        os.makedirs(output_dir)
                
                # Change to output directory for file creation
                original_cwd = os.getcwd()
                os.chdir(output_dir)
                
                try:
                    # Check if we have an API key for translation
                    try:
                        api_key = get_deepl_key()
                        has_api_key = bool(api_key)
                    except:
                        has_api_key = False
                    
                    if has_api_key and target_langs:
                        # Start translation (API key available AND target languages selected)
                        create_translation_doc(
                            self.company_name.get().strip(),
                            url_objects,
                            self.get_source_language_code(),
                            target_langs,
                            self.update_progress
                        )
                    else:
                        # Create content-only document (no API key OR no target languages selected)
                        self.create_content_only_doc(
                            self.company_name.get().strip(),
                            url_objects,
                            self.get_source_language_code(),
                            self.update_progress
                        )
                finally:
                    # Change back to original directory
                    os.chdir(original_cwd)
                
                # Update UI when complete
                self.root.after(0, self.translation_complete)
                
            except Exception as e:
                error_msg = f"Translation error: {str(e)}"
                self.root.after(0, lambda: self.show_error(error_msg))
        
        threading.Thread(target=translation_thread, daemon=True).start()
    
    def translation_complete(self):
        """Handle translation completion"""
        self.update_progress(100, "Processing complete!", "", "")
        self.clear_progress_details()
        
        # Get the output directory path (same logic as in start_translation)
        home_dir = os.path.expanduser("~")
        output_dir = os.path.join(home_dir, "Documents", "Website-Translation-Tool-Outputs")
        
        # Check if the Documents folder path exists, otherwise use fallback
        if not os.path.exists(output_dir):
            output_dir = os.path.abspath("translation_outputs")
        
        # Check which type of file was created
        try:
            api_key = get_deepl_key()
            has_api_key = bool(api_key)
        except:
            has_api_key = False
        
        # Check if target languages were selected
        target_langs = [lang for lang, var in self.target_vars.items() if var.get()]
        
        if has_api_key and target_langs:
            file_path = os.path.join(output_dir, f"{self.company_name.get()}.xlsx")
            message = f"Translation complete! File saved as:\n{file_path}\n\nWould you like to open the file location?"
        else:
            file_path = os.path.join(output_dir, f"{self.company_name.get()}_content_only.xlsx")
            message = f"Content extraction complete! File saved as:\n{file_path}\n\nWould you like to open the file location?"
        
        # Ask if user wants to open the file
        result = messagebox.askyesno("Success", message)
        
        if result:
            # Open file location
            if os.path.exists(file_path):
                os.system(f'open "{output_dir}"')
    
    def update_progress(self, percent, status="", current_url="", operation=""):
        """Update the multi-level progress display"""
        def update_ui():
            self.progress['value'] = percent
            self.progress_percent.config(text=f"{int(percent)}%")
            if status:
                self.status_label.config(text=status)
            if current_url:
                self.current_url_label.config(text=f"Current: {current_url}")
            if operation:
                self.current_operation_label.config(text=operation)
        
        self.root.after(0, update_ui)
    
    def clear_progress_details(self):
        """Clear the detailed progress information"""
        def clear_ui():
            self.current_url_label.config(text="")
            self.current_operation_label.config(text="")
        
        self.root.after(0, clear_ui)
    
    def get_source_language_code(self):
        """Extract language code from the source language selection"""
        source_value = self.source_language.get()
        # Extract just the language code (first 2 characters before the dash)
        if ' - ' in source_value:
            return source_value.split(' - ')[0]
        return source_value
    
    def show_error(self, message):
        """Show error message and reset UI"""
        self.progress['value'] = 0
        self.progress_percent.config(text="0%")
        self.status_label.config(text="Error occurred")
        self.clear_progress_details()
        messagebox.showerror("Error", message)
    
    def reset_form(self):
        """Reset all form fields for a new translation"""
        # Clear all input fields
        self.base_url.set("")
        self.company_name.set("")
        self.source_language.set("EN-US - English (US)")
        
        # Uncheck all target language checkboxes
        for var in self.target_vars.values():
            var.set(False)
        
        # Clear URL list
        self.url_listbox.delete(0, tk.END)
        self.all_urls = []
        self.selected_urls = []
        
        # Reset status
        self.update_progress(0, "Ready to start", "", "")
        self.clear_progress_details()
        
        # Focus on URL field
        self.root.focus_set()
    
    def select_all_urls(self):
        """Select all URLs in the listbox"""
        self.url_listbox.select_set(0, tk.END)
    
    def select_none_urls(self):
        """Deselect all URLs in the listbox"""
        self.url_listbox.select_clear(0, tk.END)
    
    def create_content_only_doc(self, company_name, all_urls, source_language, progress_callback=None):
        """Create Excel document with scraped content only (no translation)"""
        import xlsxwriter
        from bs4 import BeautifulSoup
        import requests
        
        # Initialize workbook
        workbook = xlsxwriter.Workbook(f'{company_name}_content_only.xlsx')
        bold = workbook.add_format({'bold': True})
        
        total_urls = len(all_urls)
        current_progress = 10  # Start at 10% after initialization
        
        # Table of contents
        if progress_callback:
            progress_callback(current_progress, "Creating table of contents...", "", "Organizing URLs...")
        
        worksheet = workbook.add_worksheet("Table of Contents")
        row, col = 0, 0
        sheet_counter = 2

        for url in all_urls:
            worksheet.write(row, col, url.address)
            worksheet.write(row, col + 1, f"Sheet {sheet_counter}")
            sheet_counter += 1
            row += 1
        
        # Process each URL
        for i, url in enumerate(all_urls):
            url_progress = 10 + (i * 80) // total_urls  # 10% to 90%
            
            if progress_callback:
                progress_callback(url_progress, f"Processing URLs ({i+1} of {total_urls})", url.address, "Fetching page...")
            try:
                # Fetch and parse the page
                if progress_callback:
                    progress_callback(url_progress + 2, f"Processing URLs ({i+1} of {total_urls})", url.address, "Parsing content...")
                
                response = requests.get(url.address)
                html_content = response.text
                soup = BeautifulSoup(html_content, 'lxml')
                
                worksheet = workbook.add_worksheet()
                
                # Add URL and language info
                worksheet.write('A1', url.address)
                worksheet.write('A2', f"Source Language: {source_language}")
                
                if progress_callback:
                    progress_callback(url_progress + 4, f"Processing URLs ({i+1} of {total_urls})", url.address, "Writing content to Excel...")
                
                # Extract content from the main section
                site_content = soup.find('main')
                title = soup.find('title')
                meta = soup.find('meta', attrs={'name':'description'})
                
                try:
                    meta_desc = meta['content'] if meta else "None"
                except:
                    meta_desc = "None"
                
                # Get ordered elements
                ordered_elements = site_content.find_all(
                    ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li']
                ) if site_content else []
                
                # Write title
                row = 3
                worksheet.write(row, 0, 'Title Tag:', bold)
                start_row = row + 1
                if title:
                    worksheet.write(start_row, 0, title.get_text().strip())
                
                # Write meta description
                row = start_row + 2
                worksheet.write(row, 0, 'Meta Description:', bold)
                start_row = row + 1
                worksheet.write(start_row, 0, meta_desc)
                
                # Write content in document order
                row = start_row + 2
                worksheet.write(row, 0, 'Content (ordered):', bold)
                start_row = row + 1
                row = start_row
                
                for element in ordered_elements:
                    try:
                        text = element.get_text().strip()
                    except:
                        text = ""
                    if not text:
                        continue
                    
                    is_heading = hasattr(element, 'name') and element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
                    
                    # Write text with formatting if heading
                    if is_heading:
                        worksheet.write(row, 0, text, bold)
                    else:
                        worksheet.write(row, 0, text)
                    row += 1
                    
            except Exception as e:
                print(f"Error processing {url.address}: {e}")
                continue
        
        if progress_callback:
            progress_callback(95, "Finalizing document...", "", "Saving Excel file...")
        
        workbook.close()
        print("Content-only document created successfully!")
        
        if progress_callback:
            progress_callback(100, "Content extraction complete!", "", "")

def main():
    root = tk.Tk()
    app = TranslationApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
