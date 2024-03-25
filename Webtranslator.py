from bs4 import BeautifulSoup
import requests  
import xlsxwriter
import deepl
from Constants import API_KEY_DEEPL

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



if __name__ == "__main__":
    company_name=input("Enter the Company Name: ")
    url = input("Enter URL to Scrape and Translate: ")
    source_language = input("Enter the current language: ")
    target_language = input("Enter Target Langauge: ") 
    

    #parses the url into BeautifulSoup
    soup = fetch_and_parse(url) 

    #finds everything in <main> of HTML file and adds the content to appropriate variables
    site_content = soup.find('main') 
    headings = site_content.find_all(['h1','h2','h3', 'h4', 'h5', 'h6']) 
    paragraphs = site_content.find_all('p')
    #lists = site_content.find_all('li')


    #initialize workbook and add a sheet

    workbook = xlsxwriter.Workbook(company_name + ' - Translation Doc.xlsx')
    worksheet = workbook.add_worksheet()

    #adds the Source language and target language to top of worksheet in columns A,B respectivly
    worksheet.write('A1', source_language)
    worksheet.write('B1', target_language)

    #sets the starting row/col for the worksheet
    row = 2
    source_column = 0
    #specifies the column where the translated content should go
    translation_column = 1
    bold = workbook.add_format({'bold':True})

    
    worksheet.write(row, source_column, 'Headings:', bold)
    row+=1
    # for each heading in the list, write the source text in column A and the translated Text in column B of the worksheet  
    for h in headings:
        hstring = h.get_text().strip()
        if hstring == '':
            continue
        else:
            worksheet.write(row, source_column, hstring)
            # h_translated = translate_text(hstring, target_language)
            # worksheet.write(row, translation_column, h_translated )
            row+=1

    row+=1
    worksheet.write(row, source_column, 'Paragraphs:', bold)
    row+=1

    #for each Paragraph in the list, write the source text in column A and the translated Text in column B of the worksheet
    for p in paragraphs:
        pstring = p.get_text().strip()
        if pstring == '':
            continue
        else:
            worksheet.write(row, source_column, pstring)
            # p_translated = translate_text(pstring, target_language)
            # worksheet.write(row,translation_column,p_translated)
            row+=1

    #save the workbook
    workbook.close()

