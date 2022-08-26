import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template
from flask.logging import default_handler
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData

# ----------------
# DB Configuration
# ----------------

# create a naming convention for the database tables
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
metadata = MetaData(naming_convention=convention)

# create instances of the Flask extensions in global scope,
# but without arguments passed in.
# These instances are not attached to the Flask app at this point.
database = SQLAlchemy(metadata=metadata)
db_migration = Migrate()

# ----------------------------
# Application Factory Function
# ----------------------------


def create_app() -> Flask:
    # create Flask application
    app = Flask(__name__)

    # configure the Flask application
    config_type = os.getenv("CONFIG_TYPE", default="config.DevelopmentConfig")
    app.config.from_object(config_type)

    initialize_extensions(app)
    register_blueprints(app)
    configure_logging(app)
    register_app_callbacks(app)
    register_error_pages(app)
    return app


# ----------------
# Helper Functions
# ----------------


def initialize_extensions(app):
    # since the app instance is now created,
    # pass it to each Flask extension instance to bind them to the app instance
    database.init_app(app)
    db_migration.init_app(app, database, render_as_batch=True)


def register_blueprints(app: Flask) -> None:
    # import the blueprints
    from project.stocks import stocks_blueprint
    from project.users import users_blueprint

    # since application instance is now available,
    # register blueprints with the Flask application instance (app)
    app.register_blueprint(stocks_blueprint)
    app.register_blueprint(users_blueprint, url_prefix="/users")


def configure_logging(app: Flask) -> None:
    # logging configuration

    # logging configuration
    file_handler = RotatingFileHandler(
        "instance/flask-stock-portfolio.log",
        maxBytes=16384,
        backupCount=20,
    )
    file_formatter = logging.Formatter(
        "%(asctime)s %(levelname)s: %(message)s [in %(filename)s:%(lineno)d]"
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    # remove the default logger configured by Flask
    app.logger.removeHandler(default_handler)

    app.logger.info("Starting the Flask Stock Portfolio App...")


def register_app_callbacks(app: Flask):
    @app.before_request
    def app_before_request():
        app.logger.info("Calling before_request() for the Flask app...")

    @app.after_request
    def app_after_request(response):
        app.logger.info("Calling after_request() for the Flask app...")
        return response

    @app.teardown_request
    def app_teardown_request(error=None):
        app.logger.info("Calling teardown_request() for the Flask app...")

    @app.teardown_appcontext
    def app_teardown_appcontext(error=None):
        app.logger.info("Calling teardown_appcontext() for the Flask app...")


def register_error_pages(app: Flask):
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return render_template("405.html"), 405
