from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange


class ScoreTemplateForm(FlaskForm):
    NAME_MAX_LENGTH = 128

    name = StringField('Имя шаблона', validators=[
        DataRequired(message='Обязательное поле'),
        Length(max=NAME_MAX_LENGTH, message=f'Поле не может содержать более {NAME_MAX_LENGTH} символов')])
    score = IntegerField('Кол-во очков', validators=[
        DataRequired(message='Обязательное поле'),
        NumberRange(min=-1000, max=1000, message='Значение должно быть от -1000 до 1000')
    ])
    submit = SubmitField('Сохранить')


class ApplyScoreTemplateForm(FlaskForm):
    submit = SubmitField('Применить')
