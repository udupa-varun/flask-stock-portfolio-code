"""
This file contains the unit tests for models.py.
"""


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
