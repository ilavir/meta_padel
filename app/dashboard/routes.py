import logging
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import bp
import sqlalchemy as sa
from app import db
from app.models import User
from app.services import role_required


logger = logging.getLogger(__name__)


@bp.route('/')
def index():
    users = db.session.scalars(sa.select(User).where(User.active)).all()
    players = [user for user in users if user.has_role('player')]
    players = sorted(users, key=lambda user: user.total_score, reverse=True)

    return render_template('dashboard/index.html', title='Рейтинг игроков', players=players)


@bp.route('/<int:user_id>/add_score')
@login_required
@role_required(['superadmin', 'admin'])
def add_score(user_id):
    user = db.get_or_404(User, user_id)

    score = request.args.get('score', None)
    comment = request.args.get('comment', None)

    user.add_score(score, comment)
    logger.info(f'Added score {score} for user "{user.username}" by {current_user.username}')
    flash(f'Добавлено {score} очков игроку "{user.name}"')
    db.session.commit()

    return redirect(url_for('dashboard.index'))
