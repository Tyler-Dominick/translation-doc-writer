from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField,SelectMultipleField,widgets
from wtforms.validators import DataRequired

LANGS= [('en', 'English'),('en-gb','English - UK'),('es', 'Spanish'),('nl', 'Dutch'),('fr', 'French'),
        ('ar', 'Arabic'), ('bg', 'Bulgarian'), ('cs','Czech'), ('da', 'Danish'),
        ('de','German'), ('el', 'Greek'), ('et', 'Estonian'), ('fi','Finnish'),
        ('hu', 'Hungarian'), ('id', 'Indonesian'), ('it', 'Italian'), ('ja','Japanese'),
        ('ko', 'Korean'), ('lt', 'Lithuanian'), ('lv','Latvian'), ('nb', 'Norwegian'),
        ('pl','Polish'), ('pt', 'Portuguese - Unspecified'),('pt-pt', 'Portuguese - Portugal'),('pt-br', 'Portuguese - Brazilian'), ('ro', 'Romanian'),('ru', 'Russian'), ('sk','Slovak'),
        ('sl', 'Slovenian'), ('sv', 'Swedish'), ('tr', 'Turkish'),('uk', 'Ukrainian'), ('zh', 'Chinese - Unspecified'),('zh-hans','Chinese - Simplified'),('zh-hant','Chinese - Traditional')]

class InputForm(FlaskForm):
    url = StringField('Url to scrape and translate', validators=[DataRequired()])
    blogs = SelectField('Include Blogs?', choices=[('yes', 'Yes'),('no', 'No')])
    submit = SubmitField('Get All Urls')

class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class TranslateForm(FlaskForm):
    company_name = StringField('Company Name', validators=[DataRequired()])
    source_lang = SelectField('Source Language', choices=LANGS)
    target_lang = MultiCheckboxField('Target Language', choices=LANGS)
    submit = SubmitField('Scrape and Translate')

