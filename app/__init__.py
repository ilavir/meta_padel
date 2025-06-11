import logging.config
from flask import Flask


logging.config.fileConfig("logging.conf")


def create_app():
    app = Flask(__name__)

    return app
