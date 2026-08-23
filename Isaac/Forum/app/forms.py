from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, BooleanField, PasswordField, SubmitField, FileField, DateField, TextAreaField
from wtforms.validators import DataRequired, Optional, Email, EqualTo, Regexp, Length, ValidationError
from flask_wtf.file import FileAllowed
from flask_login import current_user
from app import db, models
import sqlalchemy as sa
from datetime import datetime

class LoginForm(FlaskForm):
    username      = StringField('Username or Email Address', validators=[DataRequired()])
    password      = PasswordField('Password', validators=[DataRequired()])
    remember_user = BooleanField('Remember Me')
    submit        = SubmitField('Log In')