import logging
from flask import render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from . import bp
from .forms import UserAddEditForm, UserFiltersForm
from .services import get_query_param, apply_user_filters
import sqlalchemy as sa
from sqlalchemy.orm import joinedload
from app import db
from app.models import User, Role, Score, UserRankHistory
from app.services import role_required


logger = logging.getLogger(__name__)


# get all Users
@bp.route('/')
@login_required
@role_required(['superadmin', 'admin'])
def get_users():
    filters = {
        'id': get_query_param('id', int),
        'username': get_query_param('username', str),
        'email': get_query_param('email', str),
        'name': get_query_param('name', str),
        'phone': get_query_param('phone', str),
        'gender': get_query_param('gender', str),
        'active': get_query_param('active', str),
        'roles': get_query_param('roles', str)
    }
    form = UserFiltersForm(request.args)

    # Create the query with filters applied
    query = sa.select(User).options(
                joinedload(User.roles)
            )
    query = apply_user_filters(query, filters)
    users = db.session.scalars(query).unique().all()

    return render_template('users/users.html', title='Пользователи', users=users, form=form, filters=filters)


# edit User
@bp.route('/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(['superadmin', 'admin'])
def edit_user(user_id):
    user = db.get_or_404(User, user_id)

    # restrict to edit 'admin' and 'superadmin' users if you are not 'superadmin'
    if user.id != current_user.id and user.has_any_role(['superadmin', 'admin']) \
            and not current_user.has_role('superadmin'):
        flash('У вас нет прав на редактирование этого пользователя.', 'error')
        return redirect(url_for('users.get_users'))

    form = UserAddEditForm(obj=user)

    # Get all available roles
    roles = db.session.scalars(sa.select(Role)).all()

    # Form roles checkboxes list
    if current_user.has_role('superadmin'):
        form.roles.choices = [(role.id, role.name) for role in roles]
    else:
        form.roles.choices = [(role.id, role.name) for role in roles if role.name not in ['superadmin', 'admin']]

    if form.validate_on_submit():
        # update user
        user.update_from_dict(form.data)

        # Clear existing roles
        user.roles = []

        # Add selected roles
        selected_roles = db.session.scalars(sa.select(Role).where(Role.id.in_(form.roles.data))).all()
        user.roles.extend(selected_roles)

        db.session.commit()

        logger.info(f'Updated user "{user.email}"')
        flash(f'Пользовать "{user.email}" сохранен')

        return redirect(url_for('users.get_users'))

    # Pre-select current user roles
    form.roles.data = [role.id for role in user.roles]

    return render_template('users/user_add_edit.html', title='Редактировать пользователя',
                           form=form, user=user, action='edit')


# delete User
@bp.route('/<int:user_id>/delete', methods=['GET'])
@login_required
@role_required(['superadmin', 'admin'])
def delete_user(user_id):
    user = db.get_or_404(User, user_id)

    # nullify created_by for scores created by this user
    db.session.execute(
        sa.update(Score).where(Score.created_by == user.id).values(created_by=None)
    )

    # delete all scores belonging to this user
    db.session.execute(sa.delete(Score).where(Score.user_id == user.id))

    # delete all rank history for this user
    db.session.execute(sa.delete(UserRankHistory).where(UserRankHistory.user_id == user.id))

    db.session.delete(user)
    db.session.commit()
    logger.info(f'Deleted user "{user.email}"')
    flash(f'Пользователь "{user.email}" удален')

    return redirect(url_for('users.get_users'))
