import logging
from urllib.parse import urlsplit
from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user, login_user, logout_user, login_required
from . import bp
from .forms import LoginForm, RegistrationForm, EditProfileForm
import sqlalchemy as sa
from app import db
from app.models import User, Role


logger = logging.getLogger(__name__)


@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = sa.func.now()
        db.session.commit()


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('rating.index'))

    form = LoginForm()

    if form.validate_on_submit():
        logger.debug(f'Login form submitted. Email: {form.email.data}, Remember Me: {form.remember_me.data}')

        user = db.session.scalar(sa.select(User).where(User.email == form.email.data))

        # check for user/password
        if user is None or not user.check_password(form.password.data):
            flash('Неверный адрес электронной почты или пароль', 'error')
            return redirect(url_for('user.login'))

        # check if user active
        if not user.active:
            flash('Пользователь отключён', 'error')
            return redirect(url_for('user.login'))

        login_user(user, remember=form.remember_me.data)
        logger.debug(f'User {user.email} logged in')

        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('rating.index')

        return redirect(next_page)

    return render_template('user/login.html', title='Вход', form=form)


@bp.route('/logout')
def logout():
    logger.debug(f'Logout user: {current_user.email}')

    logout_user()
    flash('Вы вышли из системы')
    return redirect(url_for('user.login'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('rating.index'))

    form = RegistrationForm()

    if form.validate_on_submit():
        logger.debug(f'Registration form submitted. Email: {form.email.data}')

        # # check if there are users in DB
        # existing_user = db.session.scalar(sa.select(User))

        user = User.from_dict(form.data)
        user.roles.append(db.session.scalar(sa.select(Role).where(Role.name == 'player')))
        db.session.add(user)
        db.session.commit()

        flash('Вы успешно зарегистрированы')
        return redirect(url_for('user.login'))

    return render_template('user/register.html', title='Регистрация', form=form)


@bp.route('/me')
@login_required
def my_profile():
    scores = current_user.scores
    scores = sorted(scores, key=lambda score: score.created_at, reverse=True)

    return render_template('user/profile.html', title='Профиль', user=current_user, scores=scores)


@bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(obj=current_user)

    if form.validate_on_submit():
        logger.debug(f'Edit profile form submitted. Email: {form.email.data}')

        current_user.update_from_dict(form.data)
        db.session.commit()

        flash('Профиль обновлён')
        return redirect(url_for('user.my_profile'))

    return render_template('user/edit_profile.html', title='Редактирование профиля', form=form)
