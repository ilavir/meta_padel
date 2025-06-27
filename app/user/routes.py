import logging
from urllib.parse import urlsplit
from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import current_user, login_user, logout_user, login_required
from . import bp
from .forms import LoginForm, RegistrationForm, EditProfileForm
import sqlalchemy as sa
from app import db
from app.models import User, Role, ScoreTemplate
from app.rating.forms import ApplyScoreTemplateForm


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

        user = User.from_dict(form.data)
        user.username = form.email.data.split('@')[0][:64]
        user.roles.append(db.session.scalar(sa.select(Role).where(Role.name == 'player')))
        db.session.add(user)
        db.session.commit()

        flash('Вы успешно зарегистрированы')
        return redirect(url_for('user.login'))

    return render_template('user/register.html', title='Регистрация', form=form)


@bp.route('/<string:username>')
@login_required
def profile(username):
    user = db.session.scalar(sa.select(User).where(User.username == username))
    if user is None:
        flash('Пользователь не найден', 'error')
        return redirect(url_for('rating.index'))

    scores = user.scores
    scores = sorted(scores, key=lambda score: score.created_at, reverse=True)[:10]

    score_templates = db.session.scalars(
            sa.select(ScoreTemplate)
            .order_by(sa.desc(ScoreTemplate.score))
        ).all()
    apply_score_form = ApplyScoreTemplateForm()

    return render_template('user/profile.html', title='Профиль',
                           user=user, scores=scores,
                           score_templates=score_templates, apply_score_form=apply_score_form)


@bp.route('/me')
@login_required
def my_profile():
    scores = current_user.scores
    scores = sorted(scores, key=lambda score: score.created_at, reverse=True)[:20]

    score_templates = db.session.scalars(sa.select(ScoreTemplate)).all()
    apply_score_form = ApplyScoreTemplateForm()

    return render_template('user/profile.html', title='Профиль',
                           user=current_user, scores=scores,
                           score_templates=score_templates, apply_score_form=apply_score_form)


@bp.route('/me/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(obj=current_user)

    if form.validate_on_submit():
        logger.debug(f'Edit profile form submitted. Email: {form.email.data}')
        logger.debug(f'Form data: {form.data}')

        # Handle avatar upload
        if form.avatar.data:
            # Additional server-side file size validation
            max_size = current_app.config.get('AVATARS_MAX_CONTENT_LENGTH', 4 * 1024 * 1024)

            # Check file size
            form.avatar.data.seek(0, 2)  # Seek to end
            file_size = form.avatar.data.tell()
            form.avatar.data.seek(0)  # Seek back to beginning

            if file_size > max_size:
                size_mb = max_size / (1024 * 1024)
                flash(f'Размер файла аватара не должен превышать {size_mb:.1f} МБ', 'error')
                return render_template('user/edit_profile.html', title='Редактирование профиля', form=form)

            # Check file extension
            allowed_extensions = current_app.config.get('AVATARS_ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg'})
            filename = form.avatar.data.filename.lower()
            if not any(filename.endswith('.' + ext) for ext in allowed_extensions):
                flash('Недопустимый формат файла. Разрешены только PNG, JPG, JPEG', 'error')
                return render_template('user/edit_profile.html', title='Редактирование профиля', form=form)

            # Delete old avatar files if it's not the default
            if current_user.avatar_filename != 'default.jpg':
                User.delete_avatar_files(current_user.avatar_filename)

            # Save new avatar
            picture_file = User.save_avatar(form.avatar.data)
            current_user.avatar_filename = picture_file

        current_user.update_from_dict(form.data)
        db.session.commit()

        flash('Профиль обновлён')
        return redirect(url_for('user.my_profile'))

    return render_template('user/edit_profile.html', title='Редактирование профиля', form=form)
