from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from project import database


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

    def __init__(
        self, stock_symbol: str, number_of_shares: int, purchase_price: int
    ) -> None:
        self.stock_symbol = stock_symbol
        self.number_of_shares = int(number_of_shares)
        self.purchase_price = int(float(purchase_price) * 100)

    def __repr__(self) -> str:
        return f"{self.stock_symbol} - {self.number_of_shares} shares purchased at ${self.purchase_price / 100}"
