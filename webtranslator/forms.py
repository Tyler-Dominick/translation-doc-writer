from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired

class InputForm(FlaskForm):
    url = StringField('Url to scrape and translate', validators=[DataRequired()])
    submit = SubmitField('Get All Urls')


class TranslateForm(FlaskForm):
    company_name = StringField('Company Name', validators=[DataRequired()])
    source_lang = SelectField('Source Language', choices=[('en', 'English'),('es', 'Spanish'),('nl', 'Dutch'),('fr', 'French')])
    target_lang = SelectField('Target Language', choices=[('en', 'English'),('es', 'Spanish'),('nl', 'Dutch'),('fr', 'French')])
    submit = SubmitField('Scrape and Translate')

