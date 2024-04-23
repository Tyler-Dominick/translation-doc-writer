from bs4 import BeautifulSoup
import requests  
import xlsxwriter
import deepl
import os


auth_key = os.environ.get('API_KEY_DEEPL') 
print(auth_key)
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


def get_all_urls(base_url, ignored_urls):
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
                if loc not in ignored_urls:
                    out.add(loc)
                else:
                    continue
    return out


    
def create_translation_doc(company_name, all_urls, source_language, target_language):
    #initialize workbook and add a sheet
    workbook = xlsxwriter.Workbook('/tmp/' + company_name + ' - Translation Doc.xlsx')
    bold = workbook.add_format({'bold':True})
    title_set=set()
    title_error_counter = 0

    #parses the url into BeautifulSoup
    for url in all_urls:
            
            #sets the starting row/col for the worksheet
            row = 3
            source_column = 0
            #specifies the column where the translated content should go
            translation_column = 1
            
            soup = fetch_and_parse(url) 
            title = soup.find('title').get_text().strip()
            print('Working on: ' + title)
            
            #handles errors with worksheet titles not allowing cerrtain characters or being too long
            if len(title) >= 31:
                title=title[0:30]
            else:
                pass

            if (':' in title) or ('/' in title):
                title_error_counter += 1
                title = "title error " + str(title_error_counter)  
            else:
                pass

            if title in title_set:
                title_error_counter += 1
                title = "Duplicate title Error" + str(title_error_counter) 
            else: 
                pass

            title_set.add(title)
            print(title)
            worksheet = workbook.add_worksheet(title)


            #adds the Source language and target language to top of worksheet in columns A,B respectivly
            worksheet.write('A1', url.address)
            worksheet.write('A2', source_language)
            worksheet.write('B2', target_language)

            #finds everything in <main> of HTML file and adds the content to appropriate variables
            site_content = soup.find('main') 
            headings = site_content.find_all(['h1','h2','h3', 'h4', 'h5', 'h6']) 
            paragraphs = site_content.find_all('p')
            lists = site_content.find_all('li')

            worksheet.write(row, source_column, 'Headings:', bold)
            row+=1
            # for each heading in the list, write the source text in column A and the translated Text in column B of the worksheet  
            for h in headings:
                hstring = h.get_text().strip()
                if hstring == '':
                    continue
                else:
                    worksheet.write(row, source_column, hstring)
                    if(source_language==target_language):
                        continue
                    else:
                        h_translated = translate_text(hstring, target_language)
                        worksheet.write(row, translation_column, h_translated )
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
                    if(source_language==target_language):
                        continue
                    else:
                        p_translated = translate_text(pstring, target_language)
                        worksheet.write(row,translation_column,p_translated)
                    row+=1

            row+=1
            worksheet.write(row, source_column, 'List Elements:', bold)
            row+=1
            #for each list element in the list, write the source text in column A and the translated Text in column B of the worksheet
            for l in lists:
                lstring = l.get_text().strip()
                if lstring == '':
                    continue
                else:
                    worksheet.write(row, source_column, lstring)
                    if(source_language==target_language):
                        continue
                    else:
                        l_translated = translate_text(lstring, target_language)
                        worksheet.write(row,translation_column,l_translated)
                    row+=1

    #save the workbook
    workbook.close()
    print("Run successful!")
    return workbook


    