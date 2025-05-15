from flask_wtf import FlaskForm
from wtforms import (StringField, BooleanField, DateTimeField,
                     RadioField,SelectField,SelectMultipleField,
                     TextAreaField,SubmitField,
                     Form, Field)
from wtforms.widgets import TextInput, html_params

class filterform(FlaskForm):
    filterhost = StringField('filterhost')
    submit = SubmitField('Submit')

class edit_form(FlaskForm):
    desc = StringField('What is the new desc?')
    users = SelectMultipleField('users')
    hosts = SelectMultipleField('hosts', choices=[], validators=None)
    cmds = SelectMultipleField('cmds')
    options = SelectMultipleField('options')
    runas = SelectMultipleField('runas')
    submit = SubmitField('Submit')
