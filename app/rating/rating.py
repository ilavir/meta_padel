import logging
from datetime import datetime, timezone, timedelta
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import bp
from .services import take_rank_snapshot
from .forms import ApplyScoreTemplateForm
import sqlalchemy as sa
from app import db
from app.models import User, UserRankHistory, Score, ScoreTemplate
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

    # Fetch all previous day's ranks in a single query
    current_date = datetime.now(timezone.utc).date()
    yesterday = current_date - timedelta(days=1)

    # Get all previous ranks in one query
    previous_ranks_query = sa.select(UserRankHistory).where(
        UserRankHistory.user_id.in_([player.id for player in players]),
        UserRankHistory.rank_type == rank_type,
        sa.func.date(UserRankHistory.created_at) == yesterday
    )
    previous_ranks = db.session.scalars(previous_ranks_query).all()

    # Create a dictionary for quick lookup
    previous_ranks_dict = {rank.user_id: rank.rank for rank in previous_ranks}

    # Assign current rank and calculate rank change
    ranked_players = []
    for idx, user in enumerate(players, start=1):
        previous_rank = previous_ranks_dict.get(user.id)
        rank_change = None
        if previous_rank is not None:
            rank_change = previous_rank - idx  # Positive if moved up, negative if moved down

        ranked_players.append({
            'rank': idx,
            'rank_change': rank_change,
            'user': user
        })

    return render_template('rating/index.html', title='Рейтинг игроков', gender=gender, players=ranked_players)


@bp.route('/update-rankings')
@login_required
@role_required(['superadmin', 'admin'])
def update_rankings():
    rank_type = request.args.get('rank_type', None)
    if rank_type and rank_type not in ['male', 'female', 'all']:
        logger.error(f'Invalid Rank Type: {rank_type}')
        flash('Неверный тип рейтинга', 'error')
    elif rank_type:
        take_rank_snapshot(rank_type)
        logger.info(f'Rankings updated for {rank_type} players')
        flash('Рейтинг обновлен', 'success')
        return redirect(url_for('rating.index', gender=rank_type))

    elif not rank_type:
        take_rank_snapshot('all')
        take_rank_snapshot('male')
        take_rank_snapshot('female')
        logger.info('Rankings updated for all players')
        flash('Рейтинг обновлен', 'success')

    return redirect(url_for('rating.index'))


@bp.route('/apply-score-template', methods=['POST'])
@login_required
@role_required(['superadmin', 'admin'])
def apply_score_template():
    """Apply score template to user"""

    apply_score_form = ApplyScoreTemplateForm()
    logger.debug(f'Apply score template form submitted. Data: {request.form}')

    if apply_score_form.validate_on_submit():
        template_id = request.form.get('template_id')
        user_id = request.form.get('user_id')

        if not template_id or not user_id:
            flash('Ошибка: отсутствуют данные', 'error')
            return redirect(request.referrer or url_for('rating.index'))

        template = db.session.get(ScoreTemplate, template_id)
        user = db.session.get(User, user_id)

        if not template or not user:
            flash('Ошибка: шаблон или пользователь не найден', 'error')
            return redirect(request.referrer or url_for('rating.index'))

        # Create new score
        score = Score(
            user_id=user_id,
            score=template.score,
            comment=template.name,
            created_by=current_user.id
        )
        db.session.add(score)
        db.session.commit()

        logger.info(f'Applied score template "{template.name}" ({template.score} points) '
                    f'to user "{user.email}" by {current_user.email}')
        flash(f'Добавлено {template.score} очков игроку "{user.name}"')

        # Update rankings
        # take_rank_snapshot('all')
        # if user.gender:
        #     take_rank_snapshot(user.gender)

    return redirect(url_for('user.profile', username=user.username))


@bp.route('/delete-score/<int:score_id>')
@login_required
@role_required(['superadmin', 'admin'])
def delete_score(score_id):
    """Delete score by ID"""
    score = db.session.get(Score, score_id)
    if not score:
        flash('Начисление не найдено', 'error')
        return redirect(url_for('rating.index'))

    # Check role-based time restrictions
    if current_user.has_role('admin') and not current_user.has_role('superadmin'):
        # Admin can only delete scores from last 24 hours
        time_limit = datetime.now(timezone.utc) - timedelta(hours=24)
        score_created_at = score.created_at.replace(tzinfo=timezone.utc) \
            if score.created_at.tzinfo is None else score.created_at
        if score_created_at < time_limit:
            flash('Можно удалять только очки за последние 24 часа', 'error')
            return redirect(url_for('user.profile', username=score.user.username))

    user = score.user
    db.session.delete(score)
    db.session.commit()

    logger.info(f'Deleted score {score_id} ({score.score} points) for user "{user.email}" by {current_user.email}')
    flash(f'Удалено {score.score} очков за "{score.comment}" у игрока "{user.name}"')

    return redirect(url_for('user.profile', username=user.username))
