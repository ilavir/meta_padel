import logging
from flask import render_template
from . import bp


logger = logging.getLogger(__name__)


@bp.route('/')
def index():
    return render_template('dashboard/index.html')
