import logging
from flask import render_template, flash, redirect, url_for
from . import bp
from .forms import UserAddEditForm
import sqlalchemy as sa
from app import db
from app.models import User, Role


logger = logging.getLogger(__name__)


# get all Users
@bp.route('/')
def get_users():
    users = db.session.scalars(sa.select(User)).all()

    return render_template('users/users.html', title='Пользователи', users=users)


# edit User
@bp.route('/<int:user_id>/edit', methods=['GET', 'POST'])
def edit_user(user_id):
    user = db.get_or_404(User, user_id)
    form = UserAddEditForm(obj=user)

    # Get all available roles
    roles = db.session.scalars(sa.select(Role)).all()

    # Form roles checkboxes list
    form.roles.choices = [(role.id, role.name) for role in roles]

    if form.validate_on_submit():
        logger.debug(form.data)

        # activate/deactivate user
        user.update_from_dict(form.data)

        # Clear existing roles
        user.roles = []

        # Add selected roles
        selected_roles = db.session.scalars(sa.select(Role).where(Role.id.in_(form.roles.data))).all()
        user.roles.extend(selected_roles)

        db.session.commit()

        logger.info(f'Updated user "{user.username}"')
        flash(f'Пользовать "{user.username}" сохранен')

        return redirect(url_for('users.get_users'))

    # Pre-select current user roles
    form.roles.data = [role.id for role in user.roles]

    return render_template('users/user_add_edit.html', title='Редактировать пользователя',
                           form=form, user=user, action='edit')
