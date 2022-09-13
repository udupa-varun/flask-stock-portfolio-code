"""
This file contains the functional tests for the stocks blueprint.
"""


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
    test_client, confirm_email_default_user_logged_in
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
    test_client, log_in_default_user
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
