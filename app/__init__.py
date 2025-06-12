import os
import logging.config

from flask import Flask
from config import ProductionConfig, DevelopmentConfig, TestingConfig


logging.config.fileConfig("logging.conf")


def create_app(config_class=ProductionConfig):
    app = Flask(__name__, instance_relative_config=True)

    # Get environment from environment variable with a default value
    flask_env = os.getenv('FLASK_ENV', 'production').lower()

    try:
        if flask_env == 'development':
            app.logger.info("Development environment detected. Using DevelopmentConfig.")
            app.config.from_object(DevelopmentConfig)
        elif flask_env == 'testing':
            app.logger.info("Testing environment detected. Using TestingConfig.")
            app.config.from_object(TestingConfig)
        else:
            app.logger.info("Production environment detected. Using ProductionConfig.")
            app.config.from_object(config_class)

        # Validate critical configuration
        assert app.config.get('SECRET_KEY'), 'SECRET_KEY configuration is missing'

    except Exception as e:
        app.logger.error(f"Configuration error: {str(e)}")
        raise Exception(f"Failed to initialize application configuration: {str(e)}")

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    return app
