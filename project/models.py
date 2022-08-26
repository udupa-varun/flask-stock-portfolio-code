from project import database


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
