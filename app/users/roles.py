import logging
from flask import render_template
from . import bp
import sqlalchemy as sa
from app import db
from app.models import Role


logger = logging.getLogger(__name__)


@bp.route('/roles')
def get_roles():
    roles = db.session.scalars(sa.select(Role)).all()

    return render_template('users/roles.html', title='Роли', roles=roles)
