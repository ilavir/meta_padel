import logging
from flask import render_template
from . import bp
import sqlalchemy as sa
from app import db
from app.models import User


logger = logging.getLogger(__name__)


@bp.route('/')
def index():
    users = db.session.scalars(sa.select(User).where(User.active)).all()
    players = sorted(users, key=lambda user: user.total_score, reverse=True)

    return render_template('dashboard/index.html', title='Рейтинг игроков', players=players)
