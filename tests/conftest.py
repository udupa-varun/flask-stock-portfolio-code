from datetime import datetime

import flask
import pytest
import requests

from project import create_app, database
from project.models import Stock, User

# --------------
# Helper Classes
# --------------


class MockSuccessResponseWeekly(object):
    def __init__(self, url: str) -> None:
        self.status_code = 200
        self.url = url

    def json(self) -> dict:
        return {
            "Meta Data": {
                "2. Symbol": "AAPL",
                "3. Last Refreshed": "2022-09-20",
            },
            "Weekly Adjusted Time Series": {
                "2022-09-16": {"4. close": "379.2400"},
                "2022-09-09": {"4. close": "362.7600"},
                "2022-09-02": {"4. close": "354.3400"},
                "2022-05-06": {"4. close": "432.9800"},
            },
        }


class MockSuccessResponseDaily(object):
    def __init__(self, url) -> None:
        self.status_code = 200
        self.url = url
        self.headers = {"blaa": "1234"}

    def json(self) -> dict:
        return {
            "Meta Data": {
                "2. Symbol": "AAPL",
                "3. Last Refreshed": "2022-09-15",
            },
            "Time Series (Daily)": {
                "2022-09-15": {"4. close": "148.3400"},
                "2022-09-14": {"4. close": "135.9800"},
            },
        }


class MockApiRateLimitExceededResponse(object):
    def __init__(self, url) -> None:
        self.status_code = 200
        self.url = url
        self.headers = {"blaa": "1234"}

    def json(self) -> dict:
        return {
            "Note": "Thank you for using Alpha Vantage! Our standard API call frequency is "
            + "5 calls per minute and 500 calls per day"
        }


class MockFailedResponse(object):
    def __init__(self, url) -> None:
        self.status_code = 404
        self.url = url
        self.headers = {"blaa": "1234"}

    def json(self) -> dict:
        return {"error": "bad"}


@pytest.fixture(scope="function")
def mock_requests_get_success_weekly(monkeypatch):
    # Create a mock for the requests.get() call
    # to prevent making the actual API call
    def mock_get(url):
        return MockSuccessResponseWeekly(url)

    url = "https://alphavantage.co/query?function=TIME_SERIES_WEEKLY_ADJUSTED&symbol=MSFT&apikey=demo"
    monkeypatch.setattr(requests, "get", mock_get)


@pytest.fixture(scope="function")
def mock_requests_get_success_daily(monkeypatch):
    # Create a mock for the requests.get() call
    # to prevent making the actual API call
    def mock_get(url):
        return MockSuccessResponseDaily(url)

    url = "https://alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=MSFT&apikey=demo"
    monkeypatch.setattr(requests, "get", mock_get)


@pytest.fixture(scope="function")
def mock_requests_get_api_rate_limit_exceeded(monkeypatch):
    def mock_get(url):
        return MockApiRateLimitExceededResponse(url)

    url = "https://alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=MSFT&apikey=demo"
    monkeypatch.setattr(requests, "get", mock_get)


@pytest.fixture(scope="function")
def mock_requests_get_failure(monkeypatch):
    def mock_get(url):
        return MockFailedResponse(url)

    url = "https://alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=MSFT&apikey=demo"
    monkeypatch.setattr(requests, "get", mock_get)


@pytest.fixture(scope="function")
def new_stock():
    flask_app = create_app()
    flask_app.config.from_object("config.TestingConfig")
    flask_app.extensions["mail"].suppress = True

    # create a test client using the Flask app configured for testing
    with flask_app.test_client() as testing_client:
        # establish an application context before accessing logger and database
        with flask_app.app_context():
            stock = Stock("AAPL", "16", "406.78", 17, datetime(2022, 7, 18))
            yield stock


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
def confirm_email_default_user_logged_in(test_client, log_in_default_user):
    # mark the user as having their email confirmed
    user = User.query.filter_by(email="user@gmail.com").first()
    user.email_confirmed = True
    user.email_confirmed_on = datetime(2022, 7, 8)
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
def confirm_email_default_user_not_logged_in(
    test_client, register_default_user
):
    # mark the user as having their email confirmed
    user = User.query.filter_by(email="user@gmail.com").first()
    user.email_confirmed = True
    user.email_confirmed_on = datetime(2022, 7, 8)
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


@pytest.fixture(scope="function")
def add_stocks_for_default_user(
    test_client, confirm_email_default_user_logged_in
):
    # Add three stocks for the default user
    test_client.post(
        "/add_stock",
        data={
            "stock_symbol": "SAM",
            "number_of_shares": "27",
            "purchase_price": "301.23",
            "purchase_date": "2020-07-01",
        },
    )
    test_client.post(
        "/add_stock",
        data={
            "stock_symbol": "COST",
            "number_of_shares": "76",
            "purchase_price": "14.67",
            "purchase_date": "2019-05-26",
        },
    )
    test_client.post(
        "/add_stock",
        data={
            "stock_symbol": "TWTR",
            "number_of_shares": "146",
            "purchase_price": "34.56",
            "purchase_date": "2020-02-03",
        },
    )
    return


@pytest.fixture(scope="module")
def register_second_user(test_client):
    """
    Registers the second user using the '/users/register' route.
    """
    test_client.post(
        "/users/register",
        data={"email": "user@zmail.com", "password": "FlaskIsTheBest789"},
    )


@pytest.fixture(scope="function")
def log_in_second_user(test_client, register_second_user):
    # log in
    test_client.post(
        "/users/login",
        data={"email": "user@zmail.com", "password": "FlaskIsTheBest789"},
    )

    # this is where testing happens
    yield

    # log out the user
    test_client.get("/users/logout", follow_redirects=True)


@pytest.fixture(scope="function")
def confirm_email_second_user_logged_in(test_client, log_in_second_user):
    # mark the user as having their email confirmed
    user = User.query.filter_by(email="user@zmail.com").first()
    user.email_confirmed = True
    user.email_confirmed_on = datetime(2022, 7, 8)
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


# @pytest.fixture(scope="function")
# def confirm_email_second_user_not_logged_in(test_client, register_second_user):
#     # mark the user as having their email confirmed
#     user = User.query.filter_by(email="user@zmail.com").first()
#     user.email_confirmed = True
#     user.email_confirmed_on = datetime(2022, 7, 8)
#     database.session.add(user)
#     database.session.commit()

#     # this is where testing happens
#     yield user

#     # mark the user as having email not confirmed (cleanup)
#     user = User.query.filter_by(email="user@gmail.com").first()
#     user.email_confirmed = False
#     user.email_confirmed_on = None
#     database.session.add(user)
#     database.session.commit()
