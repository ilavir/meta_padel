import os
import logging.config

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import ProductionConfig, DevelopmentConfig, TestingConfig


logging.config.fileConfig("logging.conf")

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()


def register_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    login.login_view = 'auth.login'
    login.login_message = u"Пожалуйста, войдите в систему, чтобы получить доступ к этой странице."


def register_blueprints(app):
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.dashboard import bp as dashboard_bp
    app.register_blueprint(dashboard_bp)

    from app.users import bp as users_bp
    app.register_blueprint(users_bp, url_prefix='/users')


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # Get environment and select config class
    flask_env = os.getenv('FLASK_ENV', 'production').lower()
    config_class = {
        'development': DevelopmentConfig,
        'testing': TestingConfig
    }.get(flask_env, ProductionConfig)

    app.logger.info(f"{flask_env.capitalize()} environment detected. Using {config_class.__name__}.")
    app.config.from_object(config_class)

    # Validate critical configuration
    if not app.config.get('SECRET_KEY'):
        app.logger.error("SECRET_KEY configuration is missing")
        raise ValueError("SECRET_KEY configuration is missing")

    register_extensions(app)
    register_blueprints(app)

    return app

from app import models
