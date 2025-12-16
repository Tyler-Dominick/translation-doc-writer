"""Document creation functions for Excel output"""

import xlsxwriter
import requests
from bs4 import BeautifulSoup
from scraper import fetch_and_parse
from translator import translate_text


def write_content(worksheet, start_row, col, content, translate=False, target_language=None):
    """Write content to worksheet, optionally translating"""
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


def create_content_only_doc(company_name, all_urls, source_language, progress_callback=None):
    """Create Excel document with scraped content only (no translation)"""
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

