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
    url = "https://tylerd-training.fareharbor.me/" # <--enter URL here

    #parses the url into BeautifulSoup
    soup = fetch_and_parse(url) 

    #finds everything in <main> of HTML file and adds the content to appropriate variables
    site_content = soup.find('main') 
    headings = site_content.find_all(['h1','h2','h3', 'h4', 'h5', 'h6']) 
    paragraphs = site_content.find_all('p')
    lists = site_content.find_all('li')


    #initialize workbook and add a sheet
    workbook = xlsxwriter.Workbook('test.xlsx')
    worksheet = workbook.add_worksheet()
    target_language = 'fr' #<--- specifies target language

    #adds the Source language and target language to top of worksheet in columns A,B respectivly
    worksheet.write(0, 0, 'English')
    worksheet.write(0, 1, target_language)

    #sets the starting row/col for the worksheet
    row = 1
    col = 0

    #specifies the column where the translated content should go
    translation_column = 1

    # for each heading in the list, write the source text in column A and the translated Text in column B of the worksheet
    for h in headings:
        hstring = h.get_text().strip()
        if hstring == '':
            continue
        else:
            worksheet.write(row, col, hstring)
            h_translated = translate_text(hstring, target_language)
            worksheet.write(row, translation_column, h_translated )
            row = row + 1

    #for each Paragraph in the list, write the source text in column A and the translated Text in column B of the worksheet
    for p in paragraphs:
        pstring = p.get_text().strip()
        if pstring == '':
            continue
        else:
            worksheet.write(row, col, pstring)
            p_translated = translate_text(pstring, target_language)
            worksheet.write(row,translation_column,p_translated)
            row = row + 1

    #save the workbook
    workbook.close()

