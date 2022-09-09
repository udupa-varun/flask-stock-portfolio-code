import flask
import pytest

from datetime import datetime

from project import create_app, database
from project.models import Stock, User


@pytest.fixture(scope="module")
def new_stock():
    stock = Stock("AAPL", "16", "406.78")
    return stock


@pytest.fixture(scope="module")
def test_client():
    flask_app = create_app()
    flask_app.config.from_object("config.TestingConfig")
    flask_app.extensions["mail"].suppress = True

    # create a test client using the Flask app configured for testing
    with flask_app.test_client() as testing_client:
        # establish an application context
        with flask_app.app_context():
            flask_app.logger.info(
                "Creating database tables in the test_client() fixture..."
            )

            # create the database and the database table(s)
            database.create_all()

        # this is where testing happens
        yield testing_client

        # teardown
        with flask_app.app_context():
            database.drop_all()


@pytest.fixture(scope="module")
def register_default_user(test_client):
    # Register the default user
    test_client.post(
        "/users/register",
        data={"email": "user@gmail.com", "password": "FlaskIsAwesome123"},
        follow_redirects=True,
    )
    return


@pytest.fixture(scope="function")
def log_in_default_user(test_client, register_default_user):
    # log in the default user
    test_client.post(
        "/users/login",
        data={"email": "user@gmail.com", "password": "FlaskIsAwesome123"},
        follow_redirects=True,
    )

    # this is where testing happens
    yield

    # log out the default user
    test_client.get("/users/logout", follow_redirects=True)


@pytest.fixture(scope="module")
def new_user():
    user = User("user@gmail.com", "FlaskIsAwesome123")
    return user


@pytest.fixture(scope="function")
def confirm_email_default_user(test_client, log_in_default_user):
    # mark the user as having their email confirmed
    user = User.query.filter_by(email="user@gmail.com").first()
    user.email_confirmed = True
    user.email_confirmed_on = datetime(2020, 7, 8)
    database.session.add(user)
    database.session.commit()

    # this is where testing happens
    yield user

    # mark the user as having email not confirmed (cleanup)
    user = User.query.filter_by(email="user@gmail.com").first()
    user.email_confirmed = False
    user.email_confirmed_on = None
    database.session.add(user)
    database.session.commit()


@pytest.fixture(scope="function")
def afterwards_reset_default_user_password():
    # this is where testing happens
    yield

    # a test using this fixture could change the password for default user
    # reset it back to the default password
    user = User.query.filter_by(email="user@gmail.com").first()
    user.set_password("FlaskIsAwesome123")
    database.session.add(user)
    database.session.commit()


@pytest.fixture(scope="function")
def afterwards_reset_default_user_email():
    # this is where testing happens
    yield

    # a test using this fixture could change the email address for default user
    # reset it back to default email address
    user = User.query.filter_by(email="user.edited@gmail.com").first()
    user.set_email("user@gmail.com")
    database.session.add(user)
    database.session.commit()
