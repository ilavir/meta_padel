import logging
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TelField, EmailField, SelectMultipleField, \
    BooleanField, SelectField, widgets
from wtforms.validators import DataRequired, Length, Email


logger = logging.getLogger(__name__)


class RoleAddEditForm(FlaskForm):
    NAME_MAX_LENGTH = 64
    DESCRIPTION_MAX_LENGTH = 256

    name: StringField = StringField('Имя', validators=[
        DataRequired(message='Обязательное поле'),
        Length(max=NAME_MAX_LENGTH, message=f'Поле не может содержать более {NAME_MAX_LENGTH} символов')])
    description: StringField = StringField('Описание', validators=[
        DataRequired(message='Обязательное поле'),
        Length(max=DESCRIPTION_MAX_LENGTH, message=f'Поле не может содержать более {DESCRIPTION_MAX_LENGTH} символов')])
    submit: SubmitField = SubmitField('Сохранить')


class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class UserAddEditForm(FlaskForm):
    EMAIL_MAX_LENGTH = 128
    PASSWORD_MAX_LENGTH = 32
    NAME_MAX_LENGTH = 64
    PHONE_MAX_LENGTH = 32

    email: EmailField = EmailField('Email', validators=[
        DataRequired(message='Обязательное поле'),
        Length(max=EMAIL_MAX_LENGTH, message=f'Поле не может содержать более {EMAIL_MAX_LENGTH} символов'),
        Email(message='Некорректный адрес электронной почты')])
    name: StringField = StringField('Имя', validators=[
        DataRequired(message='Обязательное поле'),
        Length(max=NAME_MAX_LENGTH, message=f'Поле не может содержать более {NAME_MAX_LENGTH} символов')])
    phone: TelField = TelField('Телефон', validators=[
        DataRequired(message='Обязательное поле'),
        Length(max=PHONE_MAX_LENGTH, message=f'Поле не может содержать более {PHONE_MAX_LENGTH} символов')])
    gender = SelectField('Пол', choices=[('male', 'Мужской'), ('female', 'Женский')],
                         validators=[DataRequired(message='Обязательное поле')])
    active: BooleanField = BooleanField('Активен')
    roles: MultiCheckboxField = MultiCheckboxField('Роли', coerce=int)
    submit: SubmitField = SubmitField('Сохранить')
