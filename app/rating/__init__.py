from flask import Blueprint

bp = Blueprint('rating', __name__)

from app.rating import routes
