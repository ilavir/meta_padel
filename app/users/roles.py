import logging
from flask import render_template, flash, redirect, url_for
from . import bp
from .forms import RoleAddEditForm
import sqlalchemy as sa
from app import db
from app.models import Role


logger = logging.getLogger(__name__)


# get all Roles
@bp.route('/roles')
def get_roles():
    roles = db.session.scalars(sa.select(Role)).all()

    return render_template('users/roles.html', title='Роли', roles=roles)


# add new Role
@bp.route('/roles/add', methods=['GET', 'POST'])
# @login_required
# @role_required(['superadmin'])
def add_role():
    form = RoleAddEditForm()

    if form.validate_on_submit():
        # check for duplicate Role
        check_for_duplicate = db.session.scalar(sa.select(Role).where(Role.name == form.name.data))

        if check_for_duplicate:
            flash(f'Роль "{form.name.data}" уже существует', 'error')
            return redirect(url_for('users.add_role'))

        # construct data for new Role
        new_role = Role.from_dict(form.data)

        # save Role to DB
        db.session.add(new_role)
        db.session.commit()
        logger.info(f'Added new role "{new_role.name}"')
        flash(f'Роль "{new_role.name}" добавлена')

        return redirect(url_for('users.get_roles'))

    return render_template('users/role_add_edit.html', title='Добавить роль', form=form)


# edit Role
@bp.route('/roles/<int:role_id>/edit', methods=['GET', 'POST'])
# @login_required
# @role_required(['superadmin'])
def edit_role(role_id):
    role = db.get_or_404(Role, role_id)
    form = RoleAddEditForm(obj=role)

    if form.validate_on_submit():
        # check for duplicate Role
        check_for_duplicate = db.session.scalar(sa.select(Role).where(Role.name == form.name.data,
                                                                      Role.id != role.id))
        if check_for_duplicate:
            flash(f'Роль "{form.name.data}" уже существует', 'error')
            return redirect(url_for('users.edit_role', role_id=role.id))

        # update Role
        role.update_from_dict(form.data)

        db.session.commit()
        logger.info(f'Updated role "{role.name}"')
        flash(f'Роль "{role.name}" изменена')

        return redirect(url_for('users.get_roles'))

    return render_template('users/role_add_edit.html', title='Редактировать роль',
                           form=form, role=role, action='edit')


# delete Role
@bp.route('/roles/<int:role_id>/delete', methods=['GET', 'POST'])
# @login_required
# @role_required(['superadmin'])
def delete_role(role_id):
    role = db.get_or_404(Role, role_id)

    db.session.delete(role)
    db.session.commit()
    logger.info(f'Deleted role "{role.name}"')
    flash(f'Роль "{role.name}" удалена')

    return redirect(url_for('users.get_roles'))
