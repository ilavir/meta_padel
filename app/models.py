import logging
from datetime import datetime
from typing import Optional, Iterable
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

logger = logging.getLogger(__name__)


class BaseModel(db.Model):
    __abstract__ = True

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    created_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, server_default=sa.func.now())
    updated_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, server_default=sa.func.now(),
                                                       onupdate=sa.func.now())


class User(UserMixin, BaseModel):
    __tablename__ = 'users'

    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(128), index=True, unique=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(64))
    phone: so.Mapped[str] = so.mapped_column(sa.String(32))
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(128))
    active: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=False)

    roles: so.Mapped[list['Role']] = so.relationship(secondary='user_roles', back_populates='users')
    scores: so.Mapped[list['Score']] = so.relationship(back_populates='user', passive_deletes=True)

    @property
    def total_score(self):
        return sum(score.score for score in self.scores)

    def __repr__(self):
        return f'<User {self.username}>'

    def is_active(self) -> bool:
        return db.session.scalar(sa.select(User.active).where(User.id == self.id))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_role(self, role_name: str) -> bool:
        """Check if user has specific role"""
        role_names = {role.name for role in self.roles}
        return role_name in role_names

    def has_any_role(self, role_names: Iterable[str]) -> bool:
        """Check if user has any of the specified roles"""
        user_role_names = {role.name for role in self.roles}
        return bool(set(role_names) & user_role_names)

    def add_role(self, role: 'Role') -> None:
        """Add role if not already assigned"""
        if role not in self.roles:
            self.roles.append(role)

    def remove_role(self, role: 'Role') -> None:
        """Remove role if assigned"""
        if role in self.roles:
            self.roles.remove(role)


@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))


class Role(BaseModel):
    __tablename__ = 'roles'

    name: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    description: so.Mapped[str] = so.mapped_column(sa.String(256))

    users: so.Mapped[list['User']] = so.relationship(secondary='user_roles', back_populates='roles')

    def __repr__(self):
        return f'<Role {self.name}>'


class UserRole(db.Model):
    __tablename__ = 'user_roles'

    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    role_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)
    granted_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, server_default=sa.func.now())


class Score(db.Model):
    __tablename__ = 'scores'

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('users.id'), index=True)
    score: so.Mapped[int] = so.mapped_column(sa.Integer)
    comment: so.Mapped[str] = so.mapped_column(sa.String(256))
    created_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, server_default=sa.func.now())

    user: so.Mapped[User] = so.relationship(back_populates='scores')

    def __repr__(self):
        return f'<Score {self.user_id} {self.score}>'
