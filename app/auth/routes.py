import logging
from urllib.parse import urlsplit
from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user, login_user, logout_user
from . import bp
from .forms import LoginForm, RegistrationForm
import sqlalchemy as sa
from app import db
from app.models import User, Role


logger = logging.getLogger(__name__)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = LoginForm()

    if form.validate_on_submit():
        logger.debug(f'Login form submitted. Username: {form.username.data}, Remember Me: {form.remember_me.data}')

        user = db.session.scalar(sa.select(User).where(User.username == form.username.data))

        # check for user/password
        if user is None or not user.check_password(form.password.data):
            flash('Неверное имя пользователя или пароль', 'error')
            return redirect(url_for('auth.login'))

        # check if user active
        if not user.active:
            flash('Пользователь отключён', 'error')
            return redirect(url_for('auth.login'))

        login_user(user, remember=form.remember_me.data)
        logger.debug(f'User {user.username} logged in')

        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('dashboard.index')

        return redirect(next_page)

    return render_template('auth/login.html', title='Вход', form=form)


@bp.route('/logout')
def logout():
    logger.debug(f'Logout user: {current_user.username}')

    logout_user()
    flash('Вы вышли из системы')
    return redirect(url_for('auth.login'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = RegistrationForm()

    if form.validate_on_submit():
        logger.debug(f'Registration form submitted. Username: {form.username.data}')

        # # check if there are users in DB
        # existing_user = db.session.scalar(sa.select(User))

        user = User.from_dict(form.data)

        # # make user "superadmin" and active if no users in DB
        # if not existing_user:
        #     user.roles.append(db.session.scalar(sa.select(Role).where(Role.name == 'superadmin')))
        #     user.active = True

        user.roles.append(db.session.scalar(sa.select(Role).where(Role.name == 'player')))
        db.session.add(user)
        db.session.commit()

        flash('Пользователь зарегистрирован')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', title='Регистрация', form=form)
