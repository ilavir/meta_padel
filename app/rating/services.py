import logging
from datetime import datetime
import sqlalchemy as sa
from app import db
from app.models import User, UserRankHistory


logger = logging.getLogger(__name__)


def take_rank_snapshot(rank_type: str):
    """
    Calculates current ranks for a given rank_type and saves them to RankHistory.
    :param rank_type: 'all', 'male', 'female', or 'autumn_2025'
    """

    # Get active players
    users_query = sa.select(User).where(User.active)
    if rank_type in ['male', 'female']:
        users_query = users_query.where(User.gender == rank_type)

    users = db.session.scalars(users_query).all()
    players = [user for user in users if user.has_role('player')]

    # Sort by appropriate score
    if rank_type == 'autumn_2025':
        autumn_2025_start = datetime(2025, 9, 1)
        autumn_2025_end = datetime(2025, 11, 30, 23, 59, 59)

        def get_score(u):
            return sum(
                s.score for s in u.scores
                if autumn_2025_start <= s.created_at <= autumn_2025_end
            )

        players = [p for p in players if get_score(p) > 0]
    else:
        def get_score(u):
            return u.total_score

    players.sort(key=get_score, reverse=True)

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
