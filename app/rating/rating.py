import logging
from datetime import datetime, timezone, timedelta
from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from . import bp
from .services import take_rank_snapshot
from .forms import ApplyScoreTemplateForm
import sqlalchemy as sa
from app import db
from app.models import User, UserRankHistory, Score, ScoreTemplate
from app.services import role_required
from app.rating.services import get_players


logger = logging.getLogger(__name__)


@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    gender = request.args.get('gender', None)
    season = request.args.get('season', None)

    # set default season if not season and not gender
    if not gender and not season:
        season = current_app.config['DEFAULT_SEASON']

    is_season_filter = season in ['autumn_2025', 'winter_2025', 'spring_2026']
    is_gender_filter = gender in ['male', 'female']

    # Determine rank type
    rank_type = gender if is_gender_filter else season if is_season_filter else 'all'

    # Get filtered and sorted players
    players = get_players(rank_type)

    # Apply pagination to sorted results
    total = len(players)
    per_page = current_app.config['USERS_PER_PAGE']
    start = (page - 1) * per_page
    end = start + per_page
    paginated_players = players[start:end]

    # Create pagination object manually
    class SimplePagination:
        def __init__(self, page, per_page, total, items):
            self.page = page
            self.per_page = per_page
            self.total = total
            self.items = items
            self.pages = (total + per_page - 1) // per_page
            self.has_prev = page > 1
            self.has_next = page < self.pages
            self.prev_num = page - 1 if self.has_prev else None
            self.next_num = page + 1 if self.has_next else None

        def iter_pages(self, left_edge=2, left_current=2, right_current=3, right_edge=2):
            last = self.pages
            for num in range(1, last + 1):
                if num <= left_edge or \
                   (self.page - left_current - 1 < num < self.page + right_current) or \
                   num > last - right_edge:
                    yield num
                elif num == left_edge + 1 or num == last - right_edge:
                    yield None

    pagination = SimplePagination(page, per_page, total, paginated_players)

    # Get previous ranks
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).date()
    previous_ranks_query = sa.select(UserRankHistory).where(
        UserRankHistory.user_id.in_([p.id for p in paginated_players]),
        UserRankHistory.rank_type == rank_type,
        sa.func.date(UserRankHistory.created_at) == yesterday
    )
    previous_ranks_dict = {r.user_id: r.rank for r in db.session.scalars(previous_ranks_query)}

    # Build ranked players list
    rank_offset = (page - 1) * current_app.config['USERS_PER_PAGE']
    ranked_players = [{
        'rank': idx,
        'rank_change': previous_ranks_dict.get(user.id, 0) - idx if user.id in previous_ranks_dict else None,
        'user': user
    } for idx, user in enumerate(paginated_players, rank_offset + 1)]

    return render_template('rating/index.html', title='Рейтинг игроков',
                           gender=gender, season=season, players=ranked_players, pagination=pagination)


@bp.route('/update-rankings')
@login_required
@role_required(['superadmin', 'admin'])
def update_rankings():
    rank_type = request.args.get('rank_type', None)
    valid_types = ['male', 'female', 'all', 'autumn_2025', 'winter_2025', 'spring_2026']

    if rank_type and rank_type not in valid_types:
        logger.error(f'Invalid Rank Type: {rank_type}')
        flash('Неверный тип рейтинга', 'error')
    elif rank_type:
        take_rank_snapshot(rank_type)
        logger.info(f'Rankings updated for {rank_type} players')
        flash('Рейтинг обновлен', 'success')

        # Redirect to appropriate tab
        if rank_type == 'autumn_2025':
            return redirect(url_for('rating.index', season='autumn_2025'))
        elif rank_type == 'winter_2025':
            return redirect(url_for('rating.index', season='winter_2025'))
        elif rank_type == 'spring_2026':
            return redirect(url_for('rating.index', season='spring_2026'))
        elif rank_type in ['male', 'female']:
            return redirect(url_for('rating.index', gender=rank_type))
    else:
        # Update all rankings
        for rt in ['all', 'male', 'female', 'autumn_2025', 'winter_2025', 'spring_2026']:
            take_rank_snapshot(rt)
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
            logger.warning('Error applying score template: missing data')
            flash('Ошибка: отсутствуют данные', 'error')
            return redirect(request.referrer or url_for('rating.index'))

        template = db.session.get(ScoreTemplate, template_id)
        user = db.session.get(User, user_id)

        if not template or not user:
            logger.warning('Error applying score template: template or user not found')
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

    logger.warning(f'Error applying score template: {apply_score_form.errors}')
    flash('Ошибка при применении шаблона', 'error')
    return redirect(request.referrer or url_for('rating.index'))


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
