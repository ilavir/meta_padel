import logging
from datetime import datetime
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db

logger = logging.getLogger(__name__)


class BaseModel(db.Model):
    __abstract__ = True

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    created_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, server_default=sa.func.now())
    updated_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, server_default=sa.func.now(),
                                                       onupdate=sa.func.now())


class User(BaseModel):
    __tablename__ = 'users'

    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(128), index=True, unique=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(64))
    phone: so.Mapped[str] = so.mapped_column(sa.String(32))
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(128))

    def __repr__(self):
        return f'<User {self.username}>'
