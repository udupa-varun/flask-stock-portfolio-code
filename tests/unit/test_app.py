"""
This file contains unit tests for app.py
"""
from pydantic import ValidationError
from app import StockModel
import pytest


def test_validate_stock_data_nominal():
    """
    GIVEN a helper class to validate form data
    WHEN valid data is passed in
    THEN check that validation is successful
    """
    stock_data = StockModel(
        stock_symbol="SBUX",
        number_of_shares="100",
        purchase_price="45.67",
    )
    assert stock_data.stock_symbol == "SBUX"
    assert stock_data.number_of_shares == 100
    assert stock_data.purchase_price == 45.67


def test_validate_stock_data_invalid_stock_symbol():
    """
    GIVEN a helper class to validate form data
    WHEN invalid data (invalid stock symbol) is passed in
    THEN check that validation raises a ValueError
    """
    with pytest.raises(ValueError):
        stock_data = StockModel(
            stock_symbol="SBUX123",  # invalid
            number_of_shares="100",
            purchase_price="45.67",
        )


def test_validate_stock_data_invalid_number_of_shares():
    """
    GIVEN a helper class to validate form data
    WHEN invalid data (invalid number of shares) is passed in
    THEN check that validation raises a ValidationError
    """
    with pytest.raises(ValidationError):
        stock_data = StockModel(
            stock_symbol="SBUX",
            number_of_shares="100.123",  # invalid
            purchase_price="45.67",
        )


def test_validate_stock_data_invalid_purchase_price():
    """
    GIVEN a helper class to validate form data
    WHEN invalid data (invalid purchase price) is passed in
    THEN check that validation raises a ValidationError
    """
    with pytest.raises(ValidationError):
        stock_data = StockModel(
            stock_symbol="SBUX",
            number_of_shares="100",
            purchase_price="45,67",  # invalid
        )


def test_validate_stock_data_missing_inputs():
    """
    GIVEN a helper class to validate form data
    WHEN invalid data (missing inputs) is passed in
    THEN check that validation raises a ValidationError
    """
    with pytest.raises(ValidationError):
        stock_data = StockModel()  # missing input data


def test_validate_stock_data_missing_purchase_price():
    """
    GIVEN a helper class to validate form data
    WHEN invalid data (missing purchase price) is passed in
    THEN check that validation raises a ValidationError
    """
    with pytest.raises(ValidationError):
        stock_data = StockModel(
            stock_symbol="SBUX",
            number_of_shares="100",
            # missing purchase price
        )
