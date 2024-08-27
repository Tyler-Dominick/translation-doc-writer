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


def get_all_urls(base_url):
    # takes an input url and a list of ignored urls related to ComplianZ and blogs 
    # returns a set of all urls listed in sitemaps
    resp = requests.get(base_url + 'sitemap.xml')
    soup = BeautifulSoup(resp.content, 'xml')
    site_maps = soup.findAll('sitemap')
    
    out = set()

    for site_map in site_maps:
        map = site_map.find('loc').string
        if map == (base_url + "post-sitemap.xml"):
            continue
        else:
            response = requests.get(map)
            sitemap_soup = BeautifulSoup(response.content, 'xml')
            urls = sitemap_soup.findAll('url')
            for u in urls:
                loc = u.find('loc').string
                out.add(loc)
    return out



# def sanitize_title(title, title_set, title_error_counter):
#     # Handle worksheet title length and illegal characters
#     if len(title) >= 31:
#         title = title[:30]

#     for char in [':', '/', '?', '\'', '*', '[', ']']:
#         if char in title:
#             title_error_counter += 1
#             title = f"title_error_{title_error_counter}"
    
#     if title in title_set:
#         title_error_counter += 1
#         title = f"Duplicate_title_Error_{title_error_counter}"
    
#     title_set.add(title)
#     return title, title_error_counter

def write_content(worksheet, start_row, col, content, translate=False, target_language=None):
    row = start_row  # Start at the specified row
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
    workbook = xlsxwriter.Workbook(f'{company_name} - Translation Doc.xlsx')
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
        headings = site_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']) if site_content else []
        paragraphs = site_content.find_all('p') if site_content else []
        lists = site_content.find_all('li') if site_content else []

        # Write headings
        row = 3
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


# def create_translation_doc(company_name, all_urls, source_language, target_language):
#     # Initialize workbook and add a sheet
#     workbook = xlsxwriter.Workbook(f'{company_name} - Translation Doc.xlsx')
#     bold = workbook.add_format({'bold': True})

#     worksheet = workbook.add_worksheet("Table of Contents")
#     row, col = 0, 0
#     sheet_counter = 2

#     # Table of contents
#     for url in all_urls:
#         worksheet.write(row, col, url.address)
#         worksheet.write(row, col + 1, f"Sheet {sheet_counter}")
#         sheet_counter += 1
#         row += 1

#     title_set = set()
#     title_error_counter = 0
#     translate = source_language != target_language

#     for url in all_urls:
#         soup = fetch_and_parse(url)
#         title_tag = soup.find('title').get_text().strip()
#         print(f'Working on: {title_tag}')

#         # title, title_error_counter = sanitize_title(title_tag, title_set, title_error_counter)

#         worksheet = workbook.add_worksheet()

#         # Add source language and target language to the worksheet
#         worksheet.write('A1', url.address)
#         worksheet.write('A2', source_language)
#         worksheet.write('B2', target_language)

#         # Extract content from the main section of the HTML
#         site_content = soup.find('main')
#         headings = site_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']) if site_content else []
#         paragraphs = site_content.find_all('p') if site_content else []
#         lists = site_content.find_all('li') if site_content else []

#         # Write headings
#         row = 3
#         worksheet.write(row, 0, 'Headings:', bold)
#         row = write_content(worksheet, row + 1, 0, headings, translate, target_language)

#         # Write paragraphs
#         worksheet.write(row, 0, 'Paragraphs:', bold)
#         row = write_content(worksheet, row + 1, 0, paragraphs, translate, target_language)

#         # Write list elements
#         worksheet.write(row, 0, 'List Elements:', bold)
#         row = write_content(worksheet, row + 1, 0, lists, translate, target_language)

#     workbook.close()
#     print("Run successful!")
#     return workbook