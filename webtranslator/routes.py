from flask import render_template,flash, redirect, send_from_directory
from webtranslator import app, db
from webtranslator.forms import InputForm, TranslateForm
from webtranslator.translator import get_all_urls, create_translation_doc
from webtranslator.models import Webtranslation
import os



@app.route('/', methods=['GET', 'POST'])
def index():
    clear_data(db.session)
    form = InputForm()
    if form.validate_on_submit():
        i=1
        urls = get_all_urls(form.url.data)
        for u in urls:
            url_element = Webtranslation(url_num=i,address = u)
            db.session.add(url_element)
            i+=1
        db.session.commit()
        urls = Webtranslation.query.all()
        form = TranslateForm()
        return render_template('filter_urls.html', urls=urls, form=form)
    urls = Webtranslation.query.all()
    return render_template('index.html', form = form, urls = urls)

@app.route('/filter_urls', methods=['GET','POST'])
def filter_urls():
    urls = Webtranslation.query.all()
    form = TranslateForm()
    if form.validate_on_submit():
        company_name=form.company_name.data
        source_lang=form.source_lang.data
        target_lang=form.target_lang.data
        urls = Webtranslation.query.all()
        workbook = create_translation_doc(company_name=company_name, all_urls=urls, source_language=source_lang, target_language=target_lang)
        return render_template('success.html', workbook=workbook)
    return render_template('filter_urls.html', urls=urls, form=form)

@app.route('/exclude_url/<int:url_num>')
def exclude_url(url_num):
    url_to_delete = Webtranslation.query.get_or_404(url_num)
    db.session.delete(url_to_delete)
    db.session.commit()
    return redirect('/filter_urls')

@app.route('/download_link/<path:filename>', methods=['GET', 'POST'])
def download_link(filename):
   permitted_directory='/Users/tdominick/Documents/GitHub/translation-doc-writer'
   return send_from_directory(directory=permitted_directory, path=filename, as_attachment=True)





def clear_data(session):
    meta = db.metadata
    for table in reversed(meta.sorted_tables):
        print ('Clear table %s' % table)
        session.execute(table.delete())
    session.commit()
