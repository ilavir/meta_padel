from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TelField, EmailField
from wtforms.validators import DataRequired, Length, Email, EqualTo


class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired(message='Обязательное поле')])
    password = PasswordField('Пароль', validators=[DataRequired(message='Обязательное поле')])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class RegistrationForm(FlaskForm):
    USERNAME_MAX_LENGTH = 64
    PASSWORD_MAX_LENGTH = 32
    NAME_MAX_LENGTH = 64
    PHONE_MAX_LENGTH = 32
    EMAIL_MAX_LENGTH = 128

    username = StringField('Логин', validators=[
        DataRequired(message='Обязательное поле'),
        Length(max=USERNAME_MAX_LENGTH, message=f'Поле не может содержать более {USERNAME_MAX_LENGTH} символов')])
    password = PasswordField('Пароль', validators=[
        DataRequired(message='Обязательное поле'),
        Length(max=PASSWORD_MAX_LENGTH, message=f'Поле не может содержать более {PASSWORD_MAX_LENGTH} символов')])
    password2 = PasswordField('Повтор пароля', validators=[
        DataRequired(message='Обязательное поле'),
        Length(max=PASSWORD_MAX_LENGTH, message=f'Поле не может содержать более {PASSWORD_MAX_LENGTH} символов'),
        EqualTo('password', message='Пароли не совпадают')])
    name = StringField('Имя', validators=[
        DataRequired(message='Обязательное поле'),
        Length(max=NAME_MAX_LENGTH, message=f'Поле не может содержать более {NAME_MAX_LENGTH} символов')])
    phone = TelField('Телефон', validators=[
        DataRequired(message='Обязательное поле'),
        Length(max=PHONE_MAX_LENGTH, message=f'Поле не может содержать более {PHONE_MAX_LENGTH} символов')])
    email = EmailField('Email', validators=[
        DataRequired(message='Обязательное поле'),
        Length(max=EMAIL_MAX_LENGTH, message=f'Поле не может содержать более {EMAIL_MAX_LENGTH} символов'),
        Email(message='Некорректный адрес электронной почты')])
    submit = SubmitField('Зарегистрироваться')
