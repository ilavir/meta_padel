import logging
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length


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
