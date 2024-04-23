from flask import render_template,flash, redirect, send_from_directory, url_for, request, send_file
from webtranslator import app, db
from webtranslator.forms import InputForm, TranslateForm
from webtranslator.translator import *
from webtranslator.models import Webtranslation
import datetime
import xlsxwriter
import io


BLOB_READ_WRITE_TOKEN="vercel_blob_rw_RlT6FwUAO3UM0rQu_GsqGAQikcgCBFjqVgXSdxFUSn47lxA"

# Homepage route
@app.route('/', methods=['GET', 'POST'])
def index():
    # clear_data(db)
    # clears the db on each run. probably should find a better solution. used for testing. 
    form = InputForm()
    session_id = 1
    if form.validate_on_submit():
        i=1
        main_url = form.url.data
        ignored_urls = {(main_url + "disclaimer/"), (main_url + "privacy-statement-us/"), (main_url + "privacy-policy/"), (main_url + "opt-out-preferences/"), (main_url + "blog/")}
        urls = get_all_urls(form.url.data, ignored_urls)
        session_id = hash(form.url.data)
        for u in urls:
            title = get_title(u)
            url_element = Webtranslation(session_id=session_id,url_num=hash(u + str(datetime.datetime.now())),address = u, title=title)
            db.session.add(url_element)
        db.session.commit()
        urls = Webtranslation.query.filter(Webtranslation.session_id == session_id)
        print(session_id)
        for u in urls:
            print(u)
        form = TranslateForm()
        return redirect(url_for('filter_urls', session_id=session_id))
    urls = Webtranslation.query.filter(session_id == session_id)
    return render_template('index.html', form = form, urls = urls)


# Filter URLS route 
@app.route('/filter_urls/', methods=['GET','POST'])
def filter_urls():
    session_id=request.args.get('session_id')
    print(session_id)
    urls = Webtranslation.query.filter(Webtranslation.session_id == session_id)
    for u in urls:
        print(u)
    form = TranslateForm()
    if form.validate_on_submit():
        company_name=form.company_name.data
        source_lang=form.source_lang.data
        target_lang=form.target_lang.data
        urls = Webtranslation.query.filter(Webtranslation.session_id == session_id)
        # workbook = create_translation_doc(company_name=company_name, all_urls=urls, source_language=source_lang, target_language=target_lang)
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        bold = workbook.add_format({'bold':True})
        title_set=set()
        title_error_counter = 0

        #parses the url into BeautifulSoup
        for url in urls:
                
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
                worksheet.write('A2', source_lang)
                worksheet.write('B2', target_lang)

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
                        if(source_lang==target_lang):
                            continue
                        else:
                            h_translated = translate_text(hstring, target_lang)
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
                        if(source_lang==target_lang):
                            continue
                        else:
                            p_translated = translate_text(pstring, target_lang)
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
                        if(source_lang==target_lang):
                            continue
                        else:
                            l_translated = translate_text(lstring, target_lang)
                            worksheet.write(row,translation_column,l_translated)
                        row+=1

        #save the workbook
        workbook.close()

        # csv_data = output.getvalue()
        print(output)
        print("Run successful!")
        output.seek(0)
        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', download_name='test.xlsx', as_attachment=True)
        # return (render_template('success.html', workbook=workbook))
    return render_template('filter_urls.html', urls=urls, form=form)

# Exlcude URL route. Removes the url from the db and redirects back to filter urls
@app.route('/exclude_url/<url_num>')
def exclude_url(url_num):
    url_to_delete = Webtranslation.query.get_or_404(url_num)
    session = url_to_delete.session_id
    db.session.delete(url_to_delete)
    db.session.commit()
    return redirect('/filter_urls', session_id=session)

# Route for download page
@app.route('/download_link/', methods=['GET', 'POST'])
def download_link():
   filename=request.args.get('workbook')
   print(filename)
   filename=filename[5: len(filename)-1]
   print(filename)
   permitted_directory='/tmp'
   return send_from_directory(directory=permitted_directory, path=filename, as_attachment=True)

# def clear_data(session):
#     # clears the db 
#     meta = db.metadata
#     for table in reversed(meta.sorted_tables):
#         print ('Clear table %s' % table)
#         session.execute(table.delete())
#     session.commit()
