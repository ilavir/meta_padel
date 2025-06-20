import logging
import sqlalchemy as sa
from app import db
from app.models import User, UserRankHistory


logger = logging.getLogger(__name__)


def take_rank_snapshot(rank_type: str):
    """
    Calculates current ranks for a given rank_type and saves them to RankHistory.
    :param rank_type: 'all', 'male', or 'female'
    """
    logger.info(f'Taking rank snapshot for {rank_type} players...')
    if rank_type in ['male', 'female']:
        users_query = sa.select(User).where(User.active, User.gender == rank_type)
    elif rank_type == 'all':
        users_query = sa.select(User).where(User.active)
    else:
        logger.error(f'Invalid rank_type: {rank_type}')
        return {'success': False, 'message': f'Invalid rank_type: {rank_type}'}

    users = db.session.scalars(users_query).all()
    players = [user for user in users if user.has_role('player')]
    players = sorted(players, key=lambda user: user.total_score, reverse=True)

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
