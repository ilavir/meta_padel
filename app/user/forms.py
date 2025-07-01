from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TelField, \
    EmailField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
import sqlalchemy as sa
from app import db
from app.models import User
from flask_login import current_user
from flask import current_app


class FileSizeValidator:
    """Custom validator for file size"""
    def __init__(self, max_size_func=None, message=None):
        self.max_size_func = max_size_func
        if not message:
            self.message = None  # Will be set dynamically
        else:
            self.message = message

    def __call__(self, form, field):
        if field.data:
            # Get max size from config
            max_size = self.max_size_func() if callable(self.max_size_func) else self.max_size_func
            if max_size is None:
                max_size = current_app.config.get('AVATARS_MAX_CONTENT_LENGTH', 4 * 1024 * 1024)

            # Set message if not provided
            if self.message is None:
                self.message = f'Размер файла не должен превышать {self._format_size(max_size)}'

            # Get file size by seeking to end and back
            field.data.seek(0, 2)  # Seek to end
            file_size = field.data.tell()
            field.data.seek(0)  # Seek back to beginning

            if file_size > max_size:
                raise ValidationError(self.message)

    def _format_size(self, size_bytes):
        """Format bytes to human readable format"""
        if size_bytes >= 1024 * 1024:
            return f'{size_bytes / (1024 * 1024):.1f} МБ'
        elif size_bytes >= 1024:
            return f'{size_bytes / 1024:.1f} КБ'
        else:
            return f'{size_bytes} байт'


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(message='Обязательное поле')])
    password = PasswordField('Пароль', validators=[DataRequired(message='Обязательное поле')])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class RegistrationForm(FlaskForm):
    EMAIL_MAX_LENGTH = 120
    PASSWORD_MAX_LENGTH = 30
    NAME_MAX_LENGTH = 120
    PHONE_MAX_LENGTH = 30

    email = EmailField('Email', validators=[
        DataRequired(message='Обязательное поле'),
        Length(max=EMAIL_MAX_LENGTH, message=f'Поле не может содержать более {EMAIL_MAX_LENGTH} символов'),
        Email(message='Некорректный адрес электронной почты')])
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
    gender = SelectField('Пол', choices=[('', 'Выберите пол'), ('male', 'Мужской'), ('female', 'Женский')],
                         validators=[DataRequired(message='Обязательное поле')])
    submit = SubmitField('Зарегистрироваться')

    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where(User.username == username.data))
        if user is not None:
            raise ValidationError('Пожалуйста, укажите другое имя пользователя')

    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(User.email == email.data))
        if user is not None:
            raise ValidationError('Пожалуйста, укажите другой адрес электронной почты')


class EditProfileForm(FlaskForm):
    USERNAME_MAX_LENGTH = 64
    EMAIL_MAX_LENGTH = 120
    NAME_MAX_LENGTH = 120
    PHONE_MAX_LENGTH = 30
    ABOUT_ME_MAX_LENGTH = 250

    username = StringField('Логин', validators=[
        DataRequired(message='Обязательное поле'),
        Length(max=NAME_MAX_LENGTH, message=f'Поле не может содержать более {USERNAME_MAX_LENGTH} символов')])
    email = EmailField('Email', validators=[
        DataRequired(message='Обязательное поле'),
        Length(max=EMAIL_MAX_LENGTH, message=f'Поле не может содержать более {EMAIL_MAX_LENGTH} символов'),
        Email(message='Некорректный адрес электронной почты')])
    name = StringField('Имя', validators=[
        DataRequired(message='Обязательное поле'),
        Length(max=NAME_MAX_LENGTH, message=f'Поле не может содержать более {NAME_MAX_LENGTH} символов')])
    phone = TelField('Телефон', validators=[
        DataRequired(message='Обязательное поле'),
        Length(max=PHONE_MAX_LENGTH, message=f'Поле не может содержать более {PHONE_MAX_LENGTH} символов')])
    gender = SelectField('Пол', choices=[('male', 'Мужской'), ('female', 'Женский')],
                         validators=[DataRequired(message='Обязательное поле')])
    about_me = TextAreaField('О себе', validators=[
        Length(max=ABOUT_ME_MAX_LENGTH, message=f'Поле не может содержать более {ABOUT_ME_MAX_LENGTH} символов')])
    avatar = FileField('Обновить аватару',
                       validators=[
                           FileAllowed(['png', 'jpg', 'jpeg'],
                                       'Только файлы с расширениями .png, .jpg, .jpeg'),
                           FileSizeValidator()
                       ])

    submit = SubmitField('Сохранить')

    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where(sa.and_(User.username == username.data,
                                                               User.id != current_user.id)))
        if user is not None:
            raise ValidationError('Пожалуйста, укажите другое имя пользователя')

    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(sa.and_(User.email == email.data,
                                                               User.id != current_user.id)))
        if user is not None:
            raise ValidationError('Пожалуйста, укажите другой адрес электронной почты')


class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(message='Обязательное поле'),
        Email(message='Некорректный адрес электронной почты')])
    submit = SubmitField('Сбросить пароль')


class ResetPasswordForm(FlaskForm):
    PASSWORD_MAX_LENGTH = 30

    password = PasswordField('Пароль', validators=[
        DataRequired(message='Обязательное поле'),
        Length(max=PASSWORD_MAX_LENGTH, message=f'Поле не может содержать более {PASSWORD_MAX_LENGTH} символов')])
    password2 = PasswordField('Повтор пароля', validators=[
        DataRequired(message='Обязательное поле'),
        Length(max=PASSWORD_MAX_LENGTH, message=f'Поле не может содержать более {PASSWORD_MAX_LENGTH} символов'),
        EqualTo('password', message='Пароли не совпадают')])
    submit = SubmitField('Установить пароль')
