import flask
import pytest
from flask import current_app

from project import create_app, database
from project.models import Stock

@pytest.fixture(scope="module")
def new_stock():
    stock = Stock("AAPL", "16", "406.78")
    return stock


@pytest.fixture(scope="module")
def test_client():
    flask_app = create_app()
    flask_app.config.from_object("config.TestingConfig")

    # create a test client using the Flask app configured for testing
    with flask_app.test_client() as testing_client:
        # establish an application context
        with flask_app.app_context():
            flask_app.logger.info("Creating database tables in the test_client() fixture...")

            # create the database and the database table(s)
            database.create_all()

        yield testing_client

        # teardown
        with flask_app.app_context():
            database.drop_all()
