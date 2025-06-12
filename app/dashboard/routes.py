import logging
from flask import render_template
from . import bp


logger = logging.getLogger(__name__)


@bp.route('/')
def index():
    players = [
        {'name': 'John Doe', 'score': 100},
        {'name': 'Jane Smith', 'score': 90},
        {'name': 'Bob Johnson', 'score': 80},
        {'name': 'Alice Brown', 'score': 70},
        {'name': 'Superadmin', 'score': 65},
        {'name': 'Charlie Davis', 'score': 60},
        {'name': 'Eva Wilson', 'score': 50},
        {'name': 'Frank Miller', 'score': 40},
        {'name': 'Grace Lee', 'score': 30},
        {'name': 'Henry Taylor', 'score': 20},
        {'name': 'Ivy Clark', 'score': 10},
    ]
    return render_template('dashboard/index.html', title='Рейтинг игроков', players=players)
