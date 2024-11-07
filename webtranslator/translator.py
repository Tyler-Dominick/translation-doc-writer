from bs4 import BeautifulSoup
import requests  
import xlsxwriter
import deepl
from webtranslator.Constants import API_KEY_DEEPL
import threading
from webtranslator.config import shared_state, state_lock

auth_key = API_KEY_DEEPL
translator = deepl.Translator(auth_key)

def translate_text(text, target_language):
    #translates text using DeepL API
    translation = translator.translate_text(text, target_lang=target_language)
    return translation.text #returns translated text
  
def fetch_and_parse(url):
    #Fetch the HTMl content
    response = requests.get(url)
    html_content = response.text
    #parse the HTML content with BeautifulSoup
    soup = BeautifulSoup(html_content, 'lxml')
    return soup


def get_title(url):
    # gets the title tag for the filter urls page
    response = requests.get(url)
    html_content = response.text
    soup = BeautifulSoup(html_content, 'lxml')
    return soup.find('title').get_text().strip()


def get_all_urls(base_url,blogs):
    # takes an input url and a list of ignored urls related to ComplianZ and blogs 
    # returns a set of all urls listed in sitemaps
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




def write_content(worksheet, start_row, col, content, translate=False, target_language=None):
    row = start_row  # Start at the specified row
    if isinstance(content,str):
        worksheet.write(row, col, content)  # Write the original text in the specified column
        if translate:
            translated_text = translate_text(content, target_language)
            worksheet.write(row, col, translated_text)  # Write the translated text in the same row, next column
            row += 1
        return start_row, row
    else:
        for item in content:
            text = item.get_text().strip()
            if text:
                worksheet.write(row, col, text)  # Write the original text in the specified column
                if translate:
                    translated_text = translate_text(text, target_language)
                    worksheet.write(row, col, translated_text)  # Write the translated text in the same row, next column
                row += 1
        return start_row, row  # Return the starting and next available row


def create_translation_doc(company_name, all_urls, source_language, target_languages):
    global current_url
    # Initialize workbook and add a sheet
    workbook = xlsxwriter.Workbook(f'{company_name}.xlsx')
    bold = workbook.add_format({'bold': True})

    worksheet = workbook.add_worksheet("Table of Contents")
    row, col = 0, 0
    sheet_counter = 2

    # Table of contents
    for url in all_urls:
        worksheet.write(row, col, url.address)
        worksheet.write(row, col + 1, f"Sheet {sheet_counter}")
        sheet_counter += 1
        row += 1

    for url in all_urls:
        with state_lock:
            shared_state['current_url'] = f'Translating: {url.address}'
            print(f"Updated current_url to {shared_state['current_url']}")

        soup = fetch_and_parse(url.address)
        print(f'Working on: {url.address}')
        
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

        #write title
        row = 3
        worksheet.write(row, 0, 'Title Tag:', bold)
        start_row = row + 1
        _, row = write_content(worksheet, start_row, 0, title, False)
        for idx, target_language in enumerate(target_languages):
            if target_language == source_language:
                continue
            write_content(worksheet, start_row, idx + 1, title, True, target_language)  # Write translations

        #write Meta Desc
        row +=2
        worksheet.write(row, 0, 'Meta Description', bold)
        start_row = row + 1
        _, row = write_content(worksheet, start_row, 0, meta_desc, False)  # Write source headings
        for idx, target_language in enumerate(target_languages):
            if target_language == source_language:
                continue
            write_content(worksheet, start_row, idx + 1, meta_desc, True, target_language)  # Write translations

        # Write headings
        row +=2
        worksheet.write(row, 0, 'Headings:', bold)
        start_row = row + 1
        _, row = write_content(worksheet, start_row, 0, headings, False)  # Write source headings
        for idx, target_language in enumerate(target_languages):
            if target_language == source_language:
                continue
            write_content(worksheet, start_row, idx + 1, headings, True, target_language)  # Write translations

        # Write paragraphs
        row += 2  # Create some space between sections
        worksheet.write(row, 0, 'Paragraphs:', bold)
        start_row = row + 1
        _, row = write_content(worksheet, start_row, 0, paragraphs, False)  # Write source paragraphs
        for idx, target_language in enumerate(target_languages):
            if target_language == source_language:
                continue
            write_content(worksheet, start_row, idx + 1, paragraphs, True, target_language)  # Write translations

        # Write list elements
        row += 2  # Create some space between sections
        worksheet.write(row, 0, 'List Elements:', bold)
        start_row = row + 1
        _, row = write_content(worksheet, start_row, 0, lists, False)  # Write source lists
        for idx, target_language in enumerate(target_languages):
            if target_language == source_language:
                continue
            write_content(worksheet, start_row, idx + 1, lists, True, target_language)  # Write translations

    workbook.close()
    with state_lock:
        shared_state['current_url']= "Translation complete!"
        print(f"Updated current_url to: {shared_state['current_url']}")
    print("Run successful!")
    return workbook


