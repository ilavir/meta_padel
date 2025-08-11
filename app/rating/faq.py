import logging
from flask import render_template
from . import bp


logger = logging.getLogger(__name__)


@bp.route('/faq')
def faq_page():
    return render_template('faq.html')
