import logging
from flask import render_template, redirect, url_for
from . import bp
from .forms import LoginForm, RegistrationForm

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        logger.info(f'Login form submitted. Username: {form.username.data}, Remember Me: {form.remember_me.data}')
        return redirect('/')
    else:
        logger.warning(f'Login form validation failed. Errors: {form.errors}')

    return render_template('auth/login.html', title='Вход', form=form)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        logger.info(f'Registration form submitted. Username: {form.username.data}')
        return redirect(url_for('auth.login'))
    else:
        logger.warning(f'Login form validation failed. Errors: {form.errors}')

    return render_template('auth/register.html', title='Регистрация', form=form)
