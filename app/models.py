import logging
from datetime import datetime
from typing import Optional
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

    def __repr__(self):
        return f'<User {self.username}>'

    def is_active(self) -> bool:
        return db.session.scalar(sa.select(User.active).where(User.id == self.id))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))
