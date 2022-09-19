"""
This file contains the unit tests for models.py.
"""


from datetime import datetime


def test_new_user(new_user):
    """
    GIVEN a User model
    WHEN a new User is created
    THEN check the email is valid and hashed password does not equal the password provided
    """
    assert new_user.email == "user@gmail.com"
    assert new_user.password_hashed != "FlaskIsAwesome123"


def test_new_stock(new_stock):
    """
    GIVEN a Stock model
    WHEN a new Stock object is created
    THEN check the symbol, number of shares, and purchase price fields are defined correctly
    """
    assert new_stock.stock_symbol == "AAPL"
    assert new_stock.number_of_shares == 16
    assert new_stock.purchase_price == 40678
    assert new_stock.user_id == 17
    assert new_stock.purchase_date.year == 2020
    assert new_stock.purchase_date.month == 7
    assert new_stock.purchase_date.day == 18


def test_get_stock_data_success(new_stock, mock_requests_get_success_daily):
    """
    GIVEN a Flask application configured for testing and a monkeypatched version of requests.get()
    WHEN the HTTP response is set to successful
    THEN check that the stock data is updated
    """
    new_stock.get_stock_data()
    assert new_stock.stock_symbol == "AAPL"
    assert new_stock.number_of_shares == 16
    assert new_stock.purchase_price == 40678  # 406.78 -> integer
    assert new_stock.purchase_date.date() == datetime(2020, 7, 18).date()
    assert new_stock.current_price == 14834  # 148.34 -> integer
    assert new_stock.current_price_date.date() == datetime.now().date()
    assert new_stock.position_value == (14834 * 16)


def test_get_stock_data_api_rate_limit_exceeded(
    new_stock, mock_requests_get_api_rate_limit_exceeded
):
    """
    GIVEN a Flask application configured for testing and a monkeypatched version of requests.get()
    WHEN the HTTP response is set to successful but the API rate limit is exceeded
    THEN check that the stock data is not updated
    """
    new_stock.get_stock_data()
    assert new_stock.stock_symbol == "AAPL"
    assert new_stock.number_of_shares == 16
    assert new_stock.purchase_price == 40678  # 406.78 -> integer
    assert new_stock.purchase_date.date() == datetime(2020, 7, 18).date()
    assert new_stock.current_price == 0
    assert new_stock.current_price_date is None
    assert new_stock.position_value == 0


def test_get_stock_data_failure(new_stock, mock_requests_get_failure):
    """
    GIVEN a Flask application configured for testing and a monkeypatched version of requests.get()
    WHEN the HTTP response is set to failed
    THEN check that the stock data is not updated
    """
    new_stock.get_stock_data()
    assert new_stock.stock_symbol == "AAPL"
    assert new_stock.number_of_shares == 16
    assert new_stock.purchase_price == 40678  # 406.78 -> integer
    assert new_stock.purchase_date.date() == datetime(2020, 7, 18).date()
    assert new_stock.current_price == 0
    assert new_stock.current_price_date is None
    assert new_stock.position_value == 0


def test_get_stock_data_success_two_calls(
    new_stock, mock_requests_get_success_daily
):
    """
    GIVEN a Flask application configured for testing and a monkeypatched version of requests.get()
    WHEN the HTTP response is set to successful
    THEN check that the stock data is updated
    """
    assert new_stock.stock_symbol == "AAPL"
    assert new_stock.current_price == 0
    assert new_stock.current_price_date is None
    new_stock.get_stock_data()
    assert new_stock.current_price == 14834
    assert new_stock.current_price_date.date() == datetime.now().date()
    assert new_stock.position_value == (14834 * 16)
    new_stock.get_stock_data()
    assert new_stock.current_price == 14834
    assert new_stock.current_price_date.date() == datetime.now().date()
    assert new_stock.position_value == (14834 * 16)
