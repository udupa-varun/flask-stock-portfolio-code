from datetime import datetime, timedelta

import requests
from flask import current_app
from werkzeug.security import check_password_hash, generate_password_hash

from project import database


def create_alpha_vantage_url_daily_compact(symbol: str) -> str:
    return (
        f"https://alphavantage.co/query?function={'TIME_SERIES_DAILY'}"
        f"&symbol={symbol}&outputsize={'compact'}"
        f"&apikey={current_app.config['ALPHA_VANTAGE_API_KEY']}"
    )


def get_current_stock_price(symbol: str) -> float:
    current_price = 0.0
    url = create_alpha_vantage_url_daily_compact(symbol)

    # attempt the GET call to Alpha Vantage
    # check that a ConnectionError does not occur (network issue)
    try:
        r = requests.get(url)
    except requests.exceptions.ConnectionError:
        current_app.logger.warning(
            f"Error! Network problem preventing retrieving the stock data ({symbol})!"
        )
        return current_price

    if r.status_code != 200:
        current_app.logger.warning(
            f"Error! Received unexpected status code ({r.status_code}) "
            f"when retrieving daily stock data ({symbol})!"
        )
        return current_price

    daily_data = r.json()

    # check for the Time Series (Daily) key, required for processing data
    # typically missing if the API rate limit has been exceeded.
    if "Time Series (Daily)" not in daily_data:
        current_app.logger.warning(
            f"Could not find the Time Series (Daily) key"
            f"when retrieving the daily stock data ({symbol})!"
        )
        return current_price

    for element in daily_data["Time Series (Daily)"]:
        current_price = float(
            daily_data["Time Series (Daily)"][element]["4. close"]
        )
        break

    return current_price


class User(database.Model):
    """
    Class that represents a user of the application.

    The following attributes of a user are stored in this table:
        email: email address of the user
        hashed_password: hashed password using werkzeug.security
        registered_on: datetime that the user registered
        email_confirmation_sent_on: datetime that the confirmation email was sent
        email_confirmed: flag indicating if the user's email address has been confirmed
        email_confirmed_on: datetime that the user's email address was confirmed

    REMEMBER to never store the plaintext password in a database!
    """

    __tablename__ = "users"

    id = database.Column(database.Integer, primary_key="True")
    email = database.Column(database.String, unique=True)
    password_hashed = database.Column(database.String(128))
    registered_on = database.Column(database.DateTime)
    email_confirmation_sent_on = database.Column(database.DateTime)
    email_confirmed = database.Column(database.Boolean, default=False)
    email_confirmed_on = database.Column(database.DateTime)

    def __init__(self, email: str, password_plaintext: str) -> None:
        # self.email = email
        self.set_email(email)
        self.password_hashed = self._generate_password_hash(password_plaintext)
        self.registered_on = datetime.now()
        # self.email_confirmation_sent_on = datetime.now()
        # self.email_confirmed = False
        # self.email_confirmed_on = None
        stocks = database.relationship("Stock", backref="user", lazy="dynamic")

    def is_password_correct(self, password_plaintext: str):
        return check_password_hash(self.password_hashed, password_plaintext)

    @staticmethod
    def _generate_password_hash(password_plaintext: str):
        return generate_password_hash(password_plaintext)

    def __repr__(self) -> str:
        return f"<User: {self.email}>"

    @property
    def is_authenticated(self) -> bool:
        """Return true if the user has been successfully registered."""
        return True

    @property
    def is_active(self) -> bool:
        """Always True, as all users are active."""
        return True

    @property
    def is_anonymous(self) -> bool:
        """Always False, as anonymous users are not supported."""
        return False

    def get_id(self) -> str:
        """Return user ID as a unicode string."""
        return str(self.id)

    def set_password(self, password_plaintext: str):
        self.password_hashed = self._generate_password_hash(password_plaintext)

    def set_email(self, email: str):
        self.email = email
        self.email_confirmation_sent_on = datetime.now()
        self.email_confirmed = False
        self.email_confirmed_on = None


class Stock(database.Model):
    """Class that represents a purchased stock in a portfolio.

    The following attributes of a stock are stored in this table:
        stock_symbol: str
        number_of_shares: integer
        purchase_price: integer
        user_id (primary key of user that owns the stock): int
        purchase_date: datetime
        current_price: integet
        current_price_date (date when current price was retrieved from API): datetime
        position_value (current price * number of shares): int

    Note: due to a limitation in data types supported by SQLite,
    the purchase price is stored as an integer
        $24.10 -> 2410
        $100.00 -> 10000
    """

    __tablename__ = "stocks"

    id = database.Column(database.Integer, primary_key=True)
    stock_symbol = database.Column(database.String, nullable=False)
    number_of_shares = database.Column(database.Integer, nullable=False)
    purchase_price = database.Column(database.Integer, nullable=False)
    user_id = database.Column(
        database.Integer, database.ForeignKey("users.id")
    )
    purchase_date = database.Column(database.DateTime)
    current_price = database.Column(database.Integer)
    current_price_date = database.Column(database.DateTime)
    position_value = database.Column(database.Integer)

    def __init__(
        self,
        stock_symbol: str,
        number_of_shares: int,
        purchase_price: str,
        user_id: int,
        purchase_date: datetime = None,
    ) -> None:
        self.stock_symbol = stock_symbol
        self.number_of_shares = int(number_of_shares)
        self.purchase_price = int(float(purchase_price) * 100)
        self.user_id = user_id
        self.purchase_date = purchase_date
        self.current_price = 0
        self.current_price_date = None
        self.position_value = 0

    def __repr__(self) -> str:
        return f"{self.stock_symbol} - {self.number_of_shares} shares purchased at ${self.purchase_price / 100}"

    def get_stock_data(self) -> None:
        if (
            self.current_price_date is None
            or self.current_price_date.date != datetime.now().date()
        ):
            current_price = get_current_stock_price(self.stock_symbol)
            if current_price > 0.0:
                self.current_price = int(current_price * 100)
                self.current_price_date = datetime.now()
                self.position_value = (
                    self.current_price * self.number_of_shares
                )
                current_app.logger.debug(
                    f"Retrieved current price {self.current_price / 100} "
                    f"for the stock data ({self.stock_symbol})!"
                )

    def get_stock_position_value(self) -> float:
        return float(self.position_value / 100)

    def create_alpha_vantage_url_weekly(self) -> str:
        return (
            f"https://alphavantage.co/query?function={'TIME_SERIES_WEEKLY_ADJUSTED'}"
            f"&symbol={self.stock_symbol}&outputsize={'compact'}"
            f"&apikey={current_app.config['ALPHA_VANTAGE_API_KEY']}"
        )

    def get_weekly_stock_data(self) -> tuple:
        title = "Stock chart is unavailable."
        labels = []
        values = []
        url = self.create_alpha_vantage_url_weekly()

        try:
            r = requests.get(url)
        except requests.exceptions.ConnectionError:
            current_app.logger.info(
                f"Error! Network problem preventing retrieving the weekly stock data ({self.stock_symbol})!"
            )

        # status code must be 200 (OK) to process stock data
        if r.status_code != 200:
            current_app.logger.warning(
                f"Error! Received unexpected status code ({r.status_code}) "
                f"when retrieving the weekly stock data ({self.stock_symbol})!"
            )
            return title, "", ""

        weekly_data = r.json()
        # check for required key "Weekly Adjusted Time Series"
        # typically not present if API rate limit has been exceeded.
        if "Weekly Adjusted Time Series" not in weekly_data:
            current_app.logger.warning(
                f"Could not find the Weekly Adjusted Time Series key "
                f"when retrieving the weekly stock data ({self.stock_symbol})!"
            )
            return title, "", ""

        title = f"Weekly Prices ({self.stock_symbol})"

        # determine start date, either
        #   - date from 12 weeks ago if start date is less than 12 weeks ago
        #   - otherwise use purchase date
        start_date = self.purchase_date
        if (datetime.now() - start_date) < timedelta(weeks=12):
            start_date = datetime.now() - timedelta(weeks=12)

        for element in weekly_data["Weekly Adjusted Time Series"]:
            date = datetime.fromisoformat(element)
            if date.date() > start_date.date():
                labels.append(date)
                values.append(
                    weekly_data["Weekly Adjusted Time Series"][element][
                        "4. close"
                    ]
                )

        # reverse the element order as data from API is read in latest to oldest
        labels.reverse()
        values.reverse()

        return title, labels, values
