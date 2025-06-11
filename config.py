import os
from dotenv import load_dotenv

if os.environ.get('FLASK_ENV') == 'development':
    basedir = os.path.abspath(os.path.dirname(__file__))
    load_dotenv(os.path.join(basedir, '.env'), override=True)


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SESSION_COOKIE_NAME = os.environ.get('SESSION_COOKIE_NAME')


class ProductionConfig(Config):
    SENTRY_ENVIRONMENT = 'production'


class DevelopmentConfig(Config):
    SENTRY_ENVIRONMENT = 'development'


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
