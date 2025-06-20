import logging
from datetime import datetime, timezone, timedelta
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import bp
from .services import take_rank_snapshot
import sqlalchemy as sa
from app import db
from app.models import User, UserRankHistory
from app.services import role_required


logger = logging.getLogger(__name__)


@bp.route('/')
def index():
    gender = request.args.get('gender', None)

    # make users list for rating: 'male', 'female' or 'all'
    if gender in ['male', 'female']:
        rank_type = gender
        users_query = sa.select(User).where(User.active, User.gender == gender)
    else:
        rank_type = 'all'
        users_query = sa.select(User).where(User.active)

    users = db.session.scalars(users_query).all()
    players = [user for user in users if user.has_role('player')]
    players = sorted(players, key=lambda user: user.total_score, reverse=True)

    # Assign current rank and calculate rank change
    ranked_players = []
    current_date = datetime.now(timezone.utc).date()
    yesterday = current_date - timedelta(days=1)

    for idx, user in enumerate(players, start=1):
        # Get the previous day's rank from RankHistory
        previous_rank_entry = db.session.scalars(
            sa.select(UserRankHistory)
            .where(
                UserRankHistory.user_id == user.id,
                UserRankHistory.rank_type == rank_type,
                sa.func.date(UserRankHistory.created_at) == yesterday
            )
            .order_by(UserRankHistory.created_at.desc())  # In case there are multiple for yesterday, take the latest
        ).first()
        previous_rank = previous_rank_entry.rank if previous_rank_entry else None

        rank_change = None
        if previous_rank is not None:
            rank_change = previous_rank - idx  # Positive if moved up, negative if moved down

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


@bp.route('/update-rankings')
@login_required
@role_required(['superadmin', 'admin'])
def update_rankings():
    rank_type = request.args.get('rank_type', None)
    if rank_type and rank_type not in ['male', 'female', 'all']:
        return {'success': False, 'message': 'Invalid Rank Type'}
    elif rank_type:
        take_rank_snapshot(rank_type)
        logger.info(f'Rankings updated for {rank_type} players')
    elif not rank_type:
        take_rank_snapshot('all')
        take_rank_snapshot('male')
        take_rank_snapshot('female')
        logger.info('Rankings updated for all players')

    flash('Рейтинг обновлен', 'success')

    return redirect(url_for('rating.index', gender=rank_type))
