from flask import render_template,flash, redirect, send_from_directory, url_for
from webtranslator import app, db
from webtranslator.forms import InputForm, TranslateForm
from webtranslator.translator import get_all_urls, create_translation_doc, get_title
from webtranslator.models import Webtranslation
import datetime
import os


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
            i+=1
        db.session.commit()
        urls = Webtranslation.query.filter(session_id==session_id)
        form = TranslateForm()
        return redirect(url_for('filter_urls', sessionid=session_id))
    urls = Webtranslation.query.filter(session_id==session_id)
    return render_template('index.html', form = form, urls = urls)

# Filter URLS route 
@app.route('/filter_urls/<string:session_id>', methods=['GET','POST'])
def filter_urls(session_id):
    urls = Webtranslation.query.filter(session_id==session_id)
    form = TranslateForm()
    if form.validate_on_submit():
        company_name=form.company_name.data
        source_lang=form.source_lang.data
        target_lang=form.target_lang.data
        urls = Webtranslation.query.all()
        workbook = create_translation_doc(company_name=company_name, all_urls=urls, source_language=source_lang, target_language=target_lang)
        return render_template('success.html', workbook=workbook)
    return render_template('filter_urls.html', urls=urls, form=form)

# Exlcude URL route. Removes the url from the db and redirects back to filter urls
@app.route('/exclude_url/<url_num>')
def exclude_url(url_num):
    url_to_delete = Webtranslation.query.get_or_404(url_num)
    db.session.delete(url_to_delete)
    db.session.commit()
    return redirect('/filter_urls')

# Route for download page
@app.route('/download_link/<path:filename>', methods=['GET', 'POST'])
def download_link(filename):
   permitted_directory='/Users/tdominick/Documents/GitHub/translation-doc-writer'
   return send_from_directory(directory=permitted_directory, path=filename, as_attachment=True)

# def clear_data(session):
#     # clears the db 
#     meta = db.metadata
#     for table in reversed(meta.sorted_tables):
#         print ('Clear table %s' % table)
#         session.execute(table.delete())
#     session.commit()
