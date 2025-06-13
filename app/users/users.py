import logging
from flask import render_template
from . import bp
import sqlalchemy as sa
from app import db
from app.models import User


logger = logging.getLogger(__name__)


@bp.route('/')
def get_users():
    users = db.session.scalars(sa.select(User)).all()

    return render_template('users/users.html', title='Пользователи', users=users)
