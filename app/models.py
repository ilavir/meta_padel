import os
import logging
from datetime import datetime, timezone
from typing import Optional, Iterable
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db, login
from flask import url_for, current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from PIL import Image, ImageOps
import jwt

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
    name: so.Mapped[str] = so.mapped_column(sa.String(128))
    phone: so.Mapped[str] = so.mapped_column(sa.String(32))
    gender: so.Mapped[str] = so.mapped_column(sa.String(32), index=True)
    about_me: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256), default=None)
    avatar_filename: so.Mapped[str] = so.mapped_column(sa.String(64), server_default='default.jpg')
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    active: so.Mapped[bool] = so.mapped_column(sa.Boolean, default=True)
    last_seen: so.Mapped[Optional[datetime]] = so.mapped_column(sa.DateTime, default=None)

    roles: so.Mapped[list['Role']] = so.relationship(secondary='user_roles', back_populates='users')
    scores: so.Mapped[list['Score']] = so.relationship(foreign_keys='Score.user_id',
                                                       back_populates='user', passive_deletes=True)
    rank_history: so.Mapped[list['UserRankHistory']] = so.relationship(back_populates='user', passive_deletes=True)

    @property
    def total_score(self):
        return sum(score.score for score in self.scores)

    def __repr__(self):
        return f'<User {self.username}>'

    @classmethod
    def from_dict(cls, data):
        instance = cls()
        instance.update_from_dict(data)
        return instance

    def update_from_dict(self, data):
        allowed_fields = ['username', 'email', 'name', 'phone', 'gender', 'active', 'about_me']
        for field in allowed_fields:
            if field in data:
                setattr(self, field, data[field])

        if 'password' in data:
            self.set_password(data['password'])

    def is_active(self) -> bool:
        return db.session.scalar(sa.select(User.active).where(User.id == self.id))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'user_id': self.id, 'exp': int(datetime.now(timezone.utc).timestamp()) + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            user_id = jwt.decode(token, current_app.config['SECRET_KEY'],
                                 algorithms=['HS256'])['user_id']
        except Exception:
            return None
        return db.session.get(User, user_id)

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

    def add_score(self, score: int, comment: str):
        """Add score to user"""
        new_score = Score(user_id=self.id, score=score, comment=comment)
        db.session.add(new_score)

    def get_avatar_url(self, size: str = 'medium'):
        """Return the URL for the user's avatar in specified size"""

        # Size mappings
        size_suffixes = {
            'small': '_small',     # 50x50 for navigation
            'medium': '_medium',   # 100x80 for ratings
            'large': '_large',     # 300x300 for profiles
            'thumbnail': '_thumbnail'  # 30x30 for very small displays
        }

        if size not in size_suffixes:
            size = 'medium'  # Default fallback

        # Get base filename without extension
        name, ext = os.path.splitext(self.avatar_filename)
        sized_filename = f"{name}{size_suffixes[size]}{ext}"

        avatars_path = os.path.relpath(current_app.config['AVATARS_FOLDER'], current_app.static_folder)
        return url_for('static', filename=f'{avatars_path}/{sized_filename}')

    @staticmethod
    def save_avatar(form_picture):
        """Save uploaded avatar in multiple sizes and return base filename"""

        # Generate random filename
        random_hex = secrets.token_hex(8)
        _, f_ext = os.path.splitext(form_picture.filename)
        if f_ext.lower() not in current_app.config['AVATARS_ALLOWED_EXTENSIONS']:
            f_ext = '.jpg'  # Default to jpg if no valid extension

        picture_fn = random_hex + f_ext

        # Create the profile_pics directory path
        pics_dir = current_app.config['AVATARS_FOLDER']
        os.makedirs(pics_dir, exist_ok=True)

        # Open and process the image
        img = Image.open(form_picture)

        # Handle EXIF orientation to prevent rotation issues
        img = ImageOps.exif_transpose(img)

        # Convert to RGB if necessary (for PNG with transparency)
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background

        # Define sizes to generate
        sizes = current_app.config['AVATARS_SIZES']

        # Generate and save each size
        base_name = os.path.splitext(picture_fn)[0]
        for size_name, dimensions in sizes.items():
            # Create a copy of the image for this size
            img_copy = img.copy()

            # Always crop to fit exact dimensions to avoid black bars
            img_copy = User._crop_to_fit(img_copy, dimensions)

            # Save the sized image
            suffix = f"_{size_name}" if size_name != 'medium' else '_medium'
            sized_filename = f"{base_name}{suffix}{f_ext}"
            sized_path = os.path.join(pics_dir, sized_filename)

            img_copy.save(sized_path, quality=95, optimize=True)

        return picture_fn

    @staticmethod
    def _crop_to_fit(img, size):
        """Crop image to fit exact dimensions"""
        target_width, target_height = size
        img_width, img_height = img.size

        # Calculate ratios
        target_ratio = target_width / target_height
        img_ratio = img_width / img_height

        if img_ratio > target_ratio:
            # Image is wider than target - crop width
            new_width = int(img_height * target_ratio)
            left = (img_width - new_width) // 2
            img = img.crop((left, 0, left + new_width, img_height))
        else:
            # Image is taller than target - crop height
            new_height = int(img_width / target_ratio)
            top = (img_height - new_height) // 2
            img = img.crop((0, top, img_width, top + new_height))

        # Resize to exact dimensions
        return img.resize(size, Image.Resampling.LANCZOS)

    @staticmethod
    def _crop_center(img, size):
        """Crop image from center to exact dimensions"""
        img_width, img_height = img.size
        target_width, target_height = size

        left = (img_width - target_width) // 2
        top = (img_height - target_height) // 2
        right = left + target_width
        bottom = top + target_height

        return img.crop((left, top, right, bottom))

    @staticmethod
    def delete_avatar_files(avatar_filename: str):
        """Delete all sized versions of an avatar file"""
        if avatar_filename == 'default.jpg':
            return  # Don't delete default avatar

        pics_dir = current_app.config['AVATARS_FOLDER']
        base_name, ext = os.path.splitext(avatar_filename)

        # Delete all size variants
        size_suffixes = ['_thumbnail', '_small', '_medium', '_large']
        for suffix in size_suffixes:
            filename = f"{base_name}{suffix}{ext}"
            file_path = os.path.join(pics_dir, filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass


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

    @classmethod
    def from_dict(cls, data):
        instance = cls()
        instance.update_from_dict(data)
        return instance

    def update_from_dict(self, data):
        allowed_fields = ['name', 'description']
        for field in allowed_fields:
            if field in data:
                setattr(self, field, data[field])


class UserRole(db.Model):
    __tablename__ = 'user_roles'

    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    role_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)
    granted_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, server_default=sa.func.now())


class UserRankHistory(db.Model):
    __tablename__ = 'user_rank_history'

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('users.id'), index=True)
    rank_type: so.Mapped[str] = so.mapped_column(sa.String(32), index=True)
    rank: so.Mapped[int] = so.mapped_column(sa.Integer)
    created_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, server_default=sa.func.now())

    user: so.Mapped[User] = so.relationship(back_populates='rank_history')

    def __repr__(self):
        return f'<RankHistory {self.user_id} {self.rank}>'


class Score(db.Model):
    __tablename__ = 'scores'

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('users.id'), index=True)
    score: so.Mapped[int] = so.mapped_column(sa.Integer)
    comment: so.Mapped[str] = so.mapped_column(sa.String(256))
    created_by: so.Mapped[Optional[int]] = so.mapped_column(sa.ForeignKey('users.id', name='fk_scores_created_by'))
    created_at: so.Mapped[datetime] = so.mapped_column(sa.DateTime, server_default=sa.func.now())

    # Relationships
    user: so.Mapped[User] = so.relationship(foreign_keys=[user_id], back_populates='scores')
    creator: so.Mapped[User] = so.relationship(foreign_keys=[created_by])

    def __repr__(self):
        return f'<Score {self.user_id} {self.score}>'


class ScoreTemplate(BaseModel):
    __tablename__ = 'score_templates'

    name: so.Mapped[str] = so.mapped_column(sa.String(128), index=True, unique=True)
    score: so.Mapped[int] = so.mapped_column(sa.Integer)

    def __repr__(self):
        return f'<ScoreTemplate {self.name} {self.score}>'

    @classmethod
    def from_dict(cls, data):
        instance = cls()
        instance.update_from_dict(data)
        return instance

    def update_from_dict(self, data):
        allowed_fields = ['name', 'score']
        for field in allowed_fields:
            if field in data:
                setattr(self, field, data[field])
