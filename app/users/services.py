import logging
from flask import request
import sqlalchemy as sa
from app.models import User


logger = logging.getLogger(__name__)


def get_query_param(name, type_func):
    value = request.args.get(name, None)
    return type_func(value) if value not in [None, ''] else None


def apply_user_filters(query, filters):
    conditions = []

    if 'id' in filters and filters['id'] is not None:
        conditions.append(User.id == filters['id'])
    if 'username' in filters and filters['username'] is not None:
        conditions.append(User.username.ilike(f'%{filters["username"]}%'))
    if 'email' in filters and filters['email'] is not None:
        conditions.append(User.email.ilike(f'%{filters["email"]}%'))
    if 'name' in filters and filters['name'] is not None:
        conditions.append(User.name.ilike(f'%{filters["name"]}%'))
    if 'phone' in filters and filters['phone'] is not None:
        conditions.append(User.phone.ilike(f'%{filters["phone"]}%'))
    if 'gender' in filters and filters['gender'] is not None:
        conditions.append(User.gender == filters['gender'])
    if 'active' in filters and filters['active'] is not None:
        conditions.append(User.active == (filters['active'] == 'true'))
    if 'roles' in filters and filters['roles'] is not None:
        conditions.append(User.roles.any(id=filters['roles']))

    # add filters to query
    if conditions:
        query = query.where(sa.and_(*conditions))

    return query
