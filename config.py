import os
from dotenv import load_dotenv
from urllib.parse import quote

BASEDIR = os.path.abspath(os.path.dirname(__file__))

if os.environ.get('FLASK_ENV') == 'development':
    load_dotenv(os.path.join(BASEDIR, '.env'), override=True)


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SESSION_COOKIE_NAME = os.environ.get('SESSION_COOKIE_NAME')

    UPLOAD_FOLDER = os.path.join(BASEDIR, 'app', 'static', 'uploads')
    AVATARS_FOLDER = os.path.join(UPLOAD_FOLDER, 'avatars')
    AVATARS_ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    AVATARS_MAX_CONTENT_LENGTH = 4 * 1024 * 1024  # 4MB max-limit
    AVATARS_SIZES = {
            'thumbnail': (30, 30),
            'small': (100, 100),
            'medium': (200, 200),
            'large': (300, 300)
        }

    SENTRY_FLASK_DSN = os.environ.get('SENTRY_FLASK_DSN')


class ProductionConfig(Config):
    DB_HOST = os.environ.get('DATABASE_HOST')
    DB_PORT = os.environ.get('DATABASE_PORT')
    DB_USER = os.environ.get('MARIADB_USER')
    DB_PASSWORD = quote(os.environ.get('MARIADB_PASSWORD') or '')
    DB_NAME = os.environ.get('MARIADB_DATABASE')
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SENTRY_ENVIRONMENT = 'production'

    # Scheduler enabled by environment variable in production
    SCHEDULER_ENABLED = os.environ.get('SCHEDULER_ENABLED', 'false').lower() == 'true'

    # Email settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'false').lower() in ['true', '1', 'yes']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'test@example.com'


class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASEDIR, 'app.db')
    SENTRY_ENVIRONMENT = 'development'

    # Scheduler disabled in development
    SCHEDULER_ENABLED = False

    # Email settings for aiosmtpd
    MAIL_SERVER = 'localhost'
    MAIL_PORT = 8025
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'test@example.com'


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False  # Disable CSRF for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = 'test-secret-key-for-testing-only'

    # Override upload settings for testing
    UPLOAD_FOLDER = os.path.join(BASEDIR, 'tests', 'temp_uploads')
    AVATARS_FOLDER = os.path.join(BASEDIR, 'tests', 'temp_uploads', 'avatars')
    AVATARS_MAX_CONTENT_LENGTH = 1 * 1024 * 1024  # 1MB for testing

    # Disable Sentry for testing
    SENTRY_FLASK_DSN = None
    SENTRY_ENVIRONMENT = 'testing'

    # Login settings for testing
    LOGIN_DISABLED = False  # Keep login enabled for testing auth flows

    # Scheduler disabled in testing
    SCHEDULER_ENABLED = False

    # Email settings
    EMAIL_HOST = 'localhost'
    EMAIL_PORT = 8025
