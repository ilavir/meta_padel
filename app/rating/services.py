import logging
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.orm import joinedload
from app import db
from app.models import User, UserRankHistory, Role, Score


logger = logging.getLogger(__name__)


def get_season_dates(season: str):
    """
    Returns start and end dates for a given season.
    :param season: 'autumn_2025', 'winter_2025'
    :return: (start_date, end_date)
    """

    if season == 'autumn_2025':
        return datetime(2025, 9, 22), datetime(2025, 12, 26, 23, 59, 59)
    elif season == 'winter_2025':
        return datetime(2025, 12, 27), datetime(2026, 3, 20, 23, 59, 59)
    else:
        raise ValueError(f'Invalid season: {season}')


def get_users_query(rank_type: str):
    """
    Returns a query for users based on the rank_type.
    :param rank_type: 'all', 'male', 'female', 'autumn_2025', or 'winter_2025'
    :return: SQLAlchemy query
    """

    # Get active players
    users_query = (
        sa.select(User)
        .join(User.roles)
        .where(User.active, Role.name == 'player')
        .options(joinedload(User.roles), joinedload(User.scores))
    )

    if rank_type in ['male', 'female']:
        users_query = users_query.where(User.gender == rank_type)
    elif rank_type in ['autumn_2025', 'winter_2025']:
        season_start, season_end = get_season_dates(rank_type)
        users_query = users_query.join(Score, Score.user_id == User.id) \
            .where(Score.created_at.between(season_start, season_end)).distinct()

    return users_query.order_by(User.total_score.desc(), User.created_at.asc())


def get_sorted_players(users, rank_type: str):
    """
    Returns a list of players sorted by their total score.
    :param rank_type: 'all', 'male', 'female', 'autumn_2025', or 'winter_2025'
    :return: List of User objects
    """

    if rank_type in ['autumn_2025', 'winter_2025']:
        season_start, season_end = get_season_dates(rank_type)

        for user in users:
            user.display_score = sum(
                s.score for s in user.scores
                if season_start <= s.created_at <= season_end
            )
        users = [u for u in users if u.display_score > 0]
        users.sort(key=lambda u: (u.display_score, -u.created_at.timestamp()), reverse=True)
    else:
        for user in users:
            user.display_score = user.total_score

    return users


def get_players(rank_type: str):
    """
    Returns a list of players sorted by their total score.
    :param rank_type: 'all', 'male', 'female', 'autumn_2025', or 'winter_2025'
    :return: List of User objects
    """

    users_query = get_users_query(rank_type)
    users = db.session.scalars(users_query).unique().all()

    return get_sorted_players(users, rank_type)


def take_rank_snapshot(rank_type: str):
    """
    Calculates current ranks for a given rank_type and saves them to RankHistory.
    :param rank_type: 'all', 'male', 'female', 'autumn_2025', or 'winter_2025'
    """

    if rank_type not in ['all', 'male', 'female', 'autumn_2025', 'winter_2025']:
        logger.error(f'Invalid rank type: {rank_type}')
        return {'success': False, 'message': f'Invalid rank type: {rank_type}'}

    # Get filtered and sorted players
    players = get_players(rank_type)

    for idx, player in enumerate(players, start=1):
        # Create a new snapshot
        new_snapshot = UserRankHistory(
            user_id=player.id,
            rank_type=rank_type,
            rank=idx
        )
        db.session.add(new_snapshot)

    db.session.commit()
    logger.info(f'Rank snapshot taken for {rank_type}')

    return {'success': True, 'message': f'Rank snapshot taken for {rank_type}'}
