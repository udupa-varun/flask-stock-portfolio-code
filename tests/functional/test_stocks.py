"""
This file contains the functional tests for the stocks blueprint.
"""


from datetime import datetime

import pytest
import requests

# --------------
# Helper Classes
# --------------


class MockSuccessResponse(object):
    def __init__(self, url) -> None:
        self.status_code = 200
        self.url = url
        self.headers = {"blaa": "1234"}

    def json(self) -> dict:
        return {
            "Meta Data": {
                "2. Symbol": "MSFT",
                "3. Last Refreshed": "2022-09-15",
            },
            "Time Series (Daily)": {
                "2022-09-15": {"4. close": "148.3400"},
                "2022-09-14": {"4. close": "135.9800"},
            },
        }


class MockFailedResponse(object):
    def __init__(self, url) -> None:
        self.status_code = 404
        self.url = url
        self.headers = {"blaa": "1234"}

    def json(self) -> dict:
        return {"error": "bad"}


# --------------
# Test Functions
# --------------


def test_index_page(test_client):
    """
    GIVEN a Flask application
    WHEN the "/" page is requested (GET)
    THEN check if the response is valid
    """
    response = test_client.get("/")
    assert response.status_code == 200
    assert b"Flask Stock Portfolio App" in response.data
    assert b"Welcome to the" in response.data
    assert b"Flask Stock Portfolio App!" in response.data


def test_about_page(test_client):
    """
    GIVEN a Flask application
    WHEN the "/about" page is requested (GET)
    THEN check if the response is valid
    """
    response = test_client.get("/users/about")
    assert response.status_code == 200
    assert b"Flask Stock Portfolio App" in response.data
    assert b"About" in response.data
    assert (
        b"This application is built using the Flask web framework."
        in response.data
    )
    assert b"Course developed by TestDriven.io" in response.data


def test_get_add_stock_page_logged_in_confirmed(
    test_client, confirm_email_default_user_logged_in
):
    """
    GIVEN a Flask application configured for testing
        and user (confirmed) is logged in
    WHEN the "/add_stock" page is requested (GET)
    THEN check if the response is valid
    """
    response = test_client.get("/add_stock", follow_redirects=True)
    assert response.status_code == 200
    assert b"Flask Stock Portfolio App" in response.data
    assert b"Add a Stock" in response.data
    assert b"Stock Symbol: <em>(required)</em>" in response.data
    assert b"Number of Shares: <em>(required)</em>" in response.data
    assert b"Purchase Price ($): <em>(required)</em>" in response.data
    assert b"Purchase Date: <em>(required)</em>" in response.data


def test_get_add_stock_page_logged_in_not_confirmed(
    test_client, log_in_default_user
):
    """
    GIVEN a Flask application configured for testing
        and user (NOT confirmed) is logged in
    WHEN the "/add_stock" page is requested (GET)
    THEN check if the user is redirected to the 'user_profile' page
    """
    response = test_client.get("/add_stock", follow_redirects=True)
    assert response.status_code == 200
    assert b"Flask Stock Portfolio App" in response.data
    assert b"Add a Stock" not in response.data
    assert b"User Profile" in response.data
    assert b"user@gmail.com" in response.data
    assert b"Email address has not been confirmed!" in response.data


def test_get_add_stock_page_not_logged_in(test_client):
    """
    GIVEN a Flask application configured for testing
        and user is NOT logged in
    WHEN the "/add_stock" page is requested (GET)
    THEN check if the redirected to the login page
    """
    response = test_client.get("/add_stock", follow_redirects=True)
    assert response.status_code == 200
    assert b"Flask Stock Portfolio App" in response.data
    assert b"Add a Stock" not in response.data
    assert b"Please log in to access this page." in response.data
    assert b"Login" in response.data


def test_post_add_stock_page_logged_in_confirmed(
    test_client,
    confirm_email_default_user_logged_in,
    mock_requests_get_success_daily,
):
    """
    GIVEN a Flask application configured for testing
        and user (confirmed) is logged in
    WHEN the "/add_stock" page is posted to (POST)
    THEN check that the user is redirected to the 'list_stocks' page
    """
    response = test_client.post(
        "/add_stock",
        data={
            "stock_symbol": "AAPL",
            "number_of_shares": "23",
            "purchase_price": "432.17",
            "purchase_date": "2020-07-18",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"List of Stocks" in response.data
    assert b"Stock Symbol" in response.data
    assert b"Number of Shares" in response.data
    assert b"Purchase Price" in response.data
    assert b"AAPL" in response.data
    assert b"23" in response.data
    assert b"432.17" in response.data


def test_post_add_stock_page_logged_in_not_confirmed(
    test_client,
    log_in_default_user,
    mock_requests_get_success_daily,
):
    """
    GIVEN a Flask application configured for testing
        and user (not confirmed) is logged in
    WHEN the "/add_stock" page is posted to (POST)
    THEN check that the user is redirected to the 'user_profile' page
    """
    response = test_client.post(
        "/add_stock",
        data={
            "stock_symbol": "AAPL",
            "number_of_shares": "23",
            "purchase_price": "432.17",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"List of Stocks" not in response.data
    assert b"User Profile" in response.data
    assert b"user@gmail.com" in response.data
    assert b"Email address has not been confirmed!" in response.data


def test_post_add_stock_page_not_logged_in(test_client):
    """
    GIVEN a Flask application configured for testing
        and user is NOT logged in
    WHEN the "/add_stock" page is posted to (POST)
    THEN check that the user is redirected to the 'login' page
    """
    response = test_client.post(
        "/add_stock",
        data={
            "stock_symbol": "AAPL",
            "number_of_shares": "23",
            "purchase_price": "432.17",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"List of Stocks" not in response.data
    assert b"Please log in to access this page." in response.data
    assert b"Login" in response.data


def test_get_stock_list_logged_in_confirmed(
    test_client,
    add_stocks_for_default_user,
    mock_requests_get_success_daily,
):
    """
    GIVEN a Flask application configured for testing
        and user (confirmed) is logged in
        and default set of stocks in the database
    WHEN the '/stocks' page is requested (GET)
    THEN check the response is valid and each default stock is displayed
    """
    headers = [
        b"Stock Symbol",
        b"Number of Shares",
        b"Purchase Price",
        b"Purchase Date",
        b"Current Share Price",
        b"Stock Position Value",
        b"TOTAL VALUE",
    ]
    data = [
        b"SAM",
        b"27",
        b"301.23",
        b"2020-07-01",
        b"COST",
        b"76",
        b"14.67",
        b"2019-05-26",
        b"TWTR",
        b"146",
        b"34.56",
        b"2020-02-03",
    ]

    response = test_client.get("/stocks", follow_redirects=True)
    assert response.status_code == 200
    assert b"List of Stocks" in response.data
    for header in headers:
        assert header in response.data
    for element in data:
        assert element in response.data


def test_get_stock_list_logged_in_not_confirmed(
    test_client, log_in_default_user, mock_requests_get_success_daily
):
    """
    GIVEN a Flask application configured for testing
        and user (NOT confirmed) is logged in
    WHEN the '/stocks' page is requested (GET)
    THEN check the response is valid and each default stock is displayed
    """
    headers = [
        b"Stock Symbol",
        b"Number of Shares",
        b"Purchase Price",
        b"Purchase Date",
        b"Current Share Price",
        b"Stock Position Value",
        b"TOTAL VALUE",
    ]
    response = test_client.get("/stocks", follow_redirects=True)
    assert response.status_code == 200
    assert b"List of Stocks" not in response.data
    for header in headers:
        assert header not in response.data
    assert b"User Profile" in response.data
    assert b"user@gmail.com" in response.data
    assert b"Email address has not been confirmed!" in response.data


def test_get_stock_list_not_logged_in(test_client):
    """
    GIVEN a Flask application configured for testing
        and user is NOT logged in
    WHEN the '/stocks' page is requested (GET)
    THEN check the response is valid and each default stock is displayed
    """
    response = test_client.get("/stocks", follow_redirects=True)
    assert response.status_code == 200
    assert b"List of Stocks" not in response.data
    assert b"Please log in to access this page." in response.data
    assert b"Login" in response.data


def test_monkeypatch_get_success(monkeypatch):
    """
    GIVEN a Flask application and a monkeypatched version of requests.get()
    WHEN the HTTP response is set to successful
    THEN check the HTTP response
    """

    def mock_get(url):
        return MockSuccessResponse(url)

    url = "https://alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=MSFT&apikey=demo"
    monkeypatch.setattr(requests, "get", mock_get)
    r = requests.get(url)
    assert r.status_code == 200
    assert r.url == url
    assert "MSFT" in r.json()["Meta Data"]["2. Symbol"]
    assert "2022-09-15" in r.json()["Meta Data"]["3. Last Refreshed"]
    assert (
        "148.34" in r.json()["Time Series (Daily)"]["2022-09-15"]["4. close"]
    )


def test_monkeypatch_get_failure(monkeypatch):
    """
    GIVEN a Flask application and a monkeypatched version of requests.get()
    WHEN the HTTP response is set to failed
    THEN check the HTTP response
    """

    def mock_get(url):
        return MockFailedResponse(url)

    url = "https://alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=MSFT&apikey=demo"
    monkeypatch.setattr(requests, "get", mock_get)
    r = requests.get(url)
    assert r.status_code == 404
    assert r.url == url
    assert "bad" in r.json()["error"]


def test_get_stock_detail_page(
    test_client, add_stocks_for_default_user, mock_requests_get_success_weekly
):
    """
    GIVEN a Flask application configured for testing
        with the default user signed in (confirmed)
        and the default set of stocks in the database
        and a monkeypatched version of requests.get()
    WHEN the '/stocks/3' page is requested (GET) and the response from Alpha Vantage was successful
    THEN check that the response is valid including a chart
    """
    response = test_client.get("/stocks/3", follow_redirects=True)
    assert response.status_code == 200
    assert b"Stock Details" in response.data
    assert b"canvas id='stockChart'" in response.data


def test_get_stock_detail_page_failed_response(
    test_client, add_stocks_for_default_user, mock_requests_get_failure
):
    """
    GIVEN a Flask application configured for testing
        with the default user signed in (confirmed)
        and the default set of stocks in the database
        and a monkeypatched version of requests.get()
    WHEN the '/stocks/3' page is requested (GET) and the response from Alpha Vantage failed
    THEN check that the response is valid but the chart is not displayed
    """
    response = test_client.get("/stocks/3", follow_redirects=True)
    assert response.status_code == 200
    assert b"Stock Details" in response.data
    assert b"canvas id='stockChart'" not in response.data


def test_get_stock_detail_page_incorrect_user(
    test_client, confirm_email_second_user_logged_in
):
    """
    GIVEN a Flask application configured for testing
        with the second user signed in (confirmed)
    WHEN the '/stocks/3' page is requested (GET) by the incorrect user
    THEN check that a 403 error is returned
    """
    response = test_client.get("/stocks/3", follow_redirects=True)
    assert response.status_code == 403
    assert b"Stock Details" not in response.data
    assert b"canvas id='stockChart'" not in response.data


def test_get_stock_detail_page_invalid_stock(
    test_client, confirm_email_default_user_logged_in
):
    """
    GIVEN a Flask application configured for testing
        with the default user signed in (confirmed)
    WHEN the '/stocks/234' page is requested (GET)
    THEN check that a 404 error is returned
    """
    response = test_client.get("/stocks/234")
    assert response.status_code == 404
    assert b"Stock Details" not in response.data
