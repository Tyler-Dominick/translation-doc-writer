"""Main GUI application for Website Translation Tool"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
import os

# Import from our modules
from constants import LANGUAGE_NAMES
from api_key import get_deepl_key, clear_cached_key
from config import save_api_key
from updates import check_for_updates, show_update_dialog
from scraper import get_all_urls
from document_creator import create_translation_doc, create_content_only_doc
from translator import clear_translator


class TranslationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Website Translation Tool")
        
        # Get screen dimensions and set window to full width
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Set window to full width with reasonable height
        window_width = int(screen_width * .9)
        window_height = screen_height
        
        self.root.geometry(f"{window_width}x{window_height}")
        self.root.minsize(800, 600)  # Prevent window from being too small
        
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
        
        # Check for updates in background (non-blocking)
        self.check_for_updates()
        
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
        
        # Create display values for source language dropdown (using all available languages)
        source_languages = list(LANGUAGE_NAMES.keys())
        source_languages.sort()  # Sort alphabetically for better UX
        source_display_values = [f"{lang} - {LANGUAGE_NAMES[lang]}" for lang in source_languages]
        self.source_combo['values'] = source_display_values
        self.source_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 10), pady=(10, 5))
        
        ttk.Label(self.language_frame, text="Target Languages:").grid(row=1, column=0, sticky=tk.W, padx=(10, 10), pady=(5, 10))
        self.target_frame = ttk.Frame(self.language_frame)
        self.target_frame.grid(row=1, column=1, sticky=tk.W, padx=(0, 10), pady=(5, 10))
        
        # Target language checkboxes (using all available languages)
        self.target_vars = {}
        languages = list(LANGUAGE_NAMES.keys())
        languages.sort()  # Sort alphabetically for better UX
        
        for i, lang in enumerate(languages):
            var = tk.BooleanVar()
            var.trace('w', self.on_target_language_change)
            self.target_vars[lang] = var
            # Display both code and English name
            display_text = f"{lang} ({LANGUAGE_NAMES[lang]})"
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
        self.new_button.grid(row=0, column=1, padx=(0, 10))
        
        # Settings button for changing API key
        self.settings_button = ttk.Button(self.button_frame, text="Change API Key", command=self.change_api_key)
        self.settings_button.grid(row=0, column=2)
        
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
    
    def check_for_updates(self):
        """Check for app updates in background"""
        def show_update_dialog_callback(latest_version, download_url):
            """Show update dialog in main thread"""
            def show():
                show_update_dialog(self.root, latest_version, download_url)
            self.root.after(0, show)
        
        check_for_updates(show_update_dialog_callback)
    
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
                        create_content_only_doc(
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
        # Extract just the language code (first part before the dash)
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
    
    def change_api_key(self):
        """Allow user to change the DeepL API key"""
        # Prompt for new API key
        new_key = simpledialog.askstring(
            "Change DeepL API Key",
            "Enter your new DeepL API key:",
            show='*'
        )
        
        if new_key is None:
            # User cancelled
            return
        
        new_key = new_key.strip()
        
        if not new_key:
            messagebox.showwarning("Warning", "API key cannot be empty. Key not changed.")
            return
        
        # Save new key to config
        if save_api_key(new_key):
            # Clear cached key and translator to force reload
            clear_cached_key()
            clear_translator()
            
            # Update UI state
            self.check_api_key_status()
            
            messagebox.showinfo("Success", "API key updated successfully!")
        else:
            messagebox.showerror("Error", "Failed to save API key. Please try again.")
    
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


def main():
    root = tk.Tk()
    app = TranslationApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
