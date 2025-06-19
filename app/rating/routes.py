import logging
from datetime import datetime, timezone
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
    gender = request.args.get('gender', None)

    # make users list for rating: 'male', 'female' or 'all'
    if gender:
        users = db.session.scalars(sa.select(User).where(User.active, User.gender == gender)).all()
    else:
        users = db.session.scalars(sa.select(User).where(User.active)).all()

    players = [user for user in users if user.has_role('player')]
    players = sorted(players, key=lambda user: user.total_score, reverse=True)

    # Assign current rank and calculate rank change
    ranked_players = []
    for idx, user in enumerate(players, start=1):
        rank_change = None
        if user.last_rank is not None:
            rank_change = user.last_rank - idx

        ranked_players.append({
            'rank': idx,
            'rank_change': rank_change,
            'user': user
        })

    return render_template('rating/index.html', title='Рейтинг игроков', gender=gender, players=ranked_players)


@bp.route('/<int:user_id>/add_score')
@login_required
@role_required(['superadmin', 'admin'])
def add_score(user_id):
    user = db.get_or_404(User, user_id)

    score = request.args.get('score', None)
    comment = request.args.get('comment', None)

    user.add_score(score, comment)
    logger.info(f'Added score {score} for user "{user.email}" by {current_user.email}')
    flash(f'Добавлено {score} очков игроку "{user.name}"')
    db.session.commit()

    return redirect(url_for('rating.index'))


@bp.route('/_update_ranks')
def update_ranks():
    users = db.session.scalars(sa.select(User).where(User.active)).all()
    players = [user for user in users if user.has_role('player')]
    players = sorted(players, key=lambda user: user.total_score, reverse=True)

    for idx, player in enumerate(players, start=1):
        player.last_rank = idx

    db.session.commit()

    return {'success': True, 'message': 'Ranks updated successfully', 'date': datetime.now(timezone.utc)}
