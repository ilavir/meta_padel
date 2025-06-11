import logging
from flask import render_template, redirect, url_for
from . import bp
from .forms import LoginForm

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        logger.info(f'Login form submitted. Username: {form.username.data}, Remember Me: {form.remember_me.data}')
        return redirect('/')

    logger.warning('Login form validation failed. Errors: %s', form.errors)

    return render_template('auth/login.html', title='Sign In', form=form)
