import logging
from functools import wraps
from flask import abort
from flask_login import current_user


logger = logging.getLogger(__name__)


def role_required(role_names):
    """Decorator for checking user roles in Flask routes"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if not current_user.has_any_role(role_names):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator