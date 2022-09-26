import os
from datetime import timedelta

# determine path to top-level dir of this project
BASEDIR = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    FLASK_ENV = "development"
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.getenv("SECRET_KEY", default="BAD_SECRET_KEY")
    # SQLAlchemy 1.4.x has removed support for 'postgres://' URI scheme,
    # so update the URI to use 'postgres://' instead
    if os.getenv("DATABASE_URL"):
        SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL").replace(
            "postgres://", "postgresql://", 1
        )
    else:
        SQLALCHEMY_DATABASE_URI = (
            f"sqlite:///{os.path.join(BASEDIR, 'instance', 'app.db')}"
        )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    REMEMBER_COOKIE_DURATION = timedelta(days=14)

    # Flask-Mail Configuration
    MAIL_SERVER = "smtp.googlemail.com"
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", default="")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", default="")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_USERNAME", default="")

    # Alpha Vantage API Key
    ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", default="demo")

    # Logging
    LOG_TO_STDOUT = os.getenv("LOG_TO_STDOUT", default=False)


class ProductionConfig(Config):
    FLASK_ENV = "production"

    # Flask-Mail config - SendGrid
    MAIL_SERVER = "smtp.sendgrid.net"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = "apikey"
    MAIL_PASSWORD = os.getenv("SENDGRID_API_KEY", default="")


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "TEST_DATABASE_URI",
        default=f"sqlite:///{os.path.join(BASEDIR, 'instance', 'test.db')}",
    )
    WTF_CSRF_ENABLED = False
