import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))

if os.environ.get('FLASK_ENV') == 'development':
    load_dotenv(os.path.join(basedir, '.env'), override=True)


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SESSION_COOKIE_NAME = os.environ.get('SESSION_COOKIE_NAME')

    SENTRY_FLASK_DSN = os.environ.get('SENTRY_FLASK_DSN')


class ProductionConfig(Config):
    DB_HOST = os.environ.get('DATABASE_HOST')
    DB_PORT = os.environ.get('DATABASE_PORT')
    DB_USER = os.environ.get('MARIADB_USER')
    DB_PASSWORD = os.environ.get('MARIADB_PASSWORD')
    DB_NAME = os.environ.get('MARIADB_DATABASE')
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SENTRY_ENVIRONMENT = 'production'


class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SENTRY_ENVIRONMENT = 'development'


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
