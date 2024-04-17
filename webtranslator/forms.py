from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired

LANGS= [('en', 'English'),('es', 'Spanish'),('nl', 'Dutch'),('fr', 'French'),
        ('ar', 'Arabic'), ('bg', 'Bulgarian'), ('cs','Czech'), ('da', 'Danish'),
        ('de','German'), ('el', 'Greek'), ('et', 'Estonian'), ('fi','Finnish'),
        ('hu', 'Hungarian'), ('id', 'Indonesian'), ('it', 'Italian'), ('ja','Japanese'),
        ('ko', 'Korean'), ('lt', 'Lithuanian'), ('lv','Latvian'), ('nb', 'Norwegian'),
        ('pl','Polish'), ('pt', 'Portuguese'), ('ro', 'Romanian'), ('sk','Slovak'),
        ('sl', 'Slovenian'), ('sv', 'Swedish'), ('tr', 'Turkish'),('uk', 'Ukrainian'), ('zh', 'Chinese')]

class InputForm(FlaskForm):
    url = StringField('Url to scrape and translate', validators=[DataRequired()])
    submit = SubmitField('Get All Urls')


class TranslateForm(FlaskForm):
    company_name = StringField('Company Name', validators=[DataRequired()])
    source_lang = SelectField('Source Language', choices=LANGS)
    target_lang = SelectField('Target Language', choices=LANGS)
    submit = SubmitField('Scrape and Translate')

