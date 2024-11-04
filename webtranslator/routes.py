from flask import render_template,flash,session, redirect, send_from_directory, url_for, request, jsonify
# from werkzeug.utils import safe_join
from webtranslator import app, db
from webtranslator.forms import InputForm, TranslateForm
from webtranslator.translator import get_all_urls, create_translation_doc, get_title
from webtranslator.models import Webtranslation
import os
import threading
from webtranslator.config import shared_state, state_lock



# Homepage route
@app.route('/', methods=['GET', 'POST'])
def index():
    clear_data(db.session)
    # clears the db on each run. probably should find a better solution. used for testing. 
    form = InputForm()
    if form.validate_on_submit():
        i=1
        urls = get_all_urls(form.url.data,form.blogs.data)
        for u in urls:
            url_element = Webtranslation(url_num=i,address = u)
            db.session.add(url_element)
            i+=1
        db.session.commit()
        return redirect(url_for('filter_urls'))
    urls = Webtranslation.query.all()
    return render_template('index.html', form = form, urls = urls)

# Filter URLS route 
@app.route('/filter_urls', methods=['GET','POST'])
def filter_urls():
    urls = Webtranslation.query.all()
    form = TranslateForm()
    if form.validate_on_submit():
        session['company_name']=form.company_name.data
        session['source_lang']=form.source_lang.data
        session['target_langs']=form.target_lang.data
        # urls = Webtranslation.query.all()
        
        return redirect(url_for('translation_progress'))
    return render_template('filter_urls.html', urls=urls, form=form)

# Exlcude URL route. Removes the url from the db and redirects back to filter urls
@app.route('/exclude_url', methods=['POST'])
def exclude_url():
    excluded_urls = request.form.getlist('exclude')
    if excluded_urls:
        Webtranslation.query.filter(Webtranslation.url_num.in_(excluded_urls)).delete(synchronize_session=False)
        db.session.commit()
    return redirect(url_for('filter_urls'))


# Route for download page
@app.route('/download_link/<path:filename>', methods=['GET', 'POST'])
def download_link(filename):
   permitted_directory='/Users/tdominick/Documents/GitHub/translation-doc-writer'
   return send_from_directory(directory=permitted_directory, path=filename, as_attachment=True)



def clear_data(session):
    # clears the db 
    meta = db.metadata
    for table in reversed(meta.sorted_tables):
        print ('Clear table %s' % table)
        session.execute(table.delete())
    session.commit()

@app.route('/current_url')
def get_current_url():
    with state_lock:
        current_url = shared_state['current_url']
    print(f"Route Accessed current_url: {current_url}")
    return jsonify({"current_url": current_url})

@app.route('/translation_progress')
def translation_progress():
    company_name = session.get('company_name')
    urls = Webtranslation.query.all()
    source_lang = session.get('source_lang')
    target_langs = session.get('target_langs')

    # Start translation in a separate thread
    thread = threading.Thread(target=create_translation_doc, args=(company_name, urls, source_lang, target_langs))
    thread.start()
    # Render the template first
    workbook_filename = f'{company_name} - Translation Doc.xlsx'
    return render_template('translation_progress.html', workbook_filename=workbook_filename)
