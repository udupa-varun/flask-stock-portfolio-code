import click
from flask import (
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required
from functools import wraps
from pydantic import BaseModel, ValidationError, validator

from project import database
from project.models import Stock

from . import stocks_blueprint

# ------------
# CLI Commands
# ------------


@stocks_blueprint.cli.command("create_default_set")
def create_default_set():
    """
    Create three new stocks and add them to the database
    """
    stock1 = Stock("HD", "25", "247.29")
    stock2 = Stock("TWTR", "230", "31.89")
    stock3 = Stock("DIS", "65", "118.77")
    database.session.add(stock1)
    database.session.add(stock2)
    database.session.add(stock3)
    database.session.commit()


@stocks_blueprint.cli.command("create")
@click.argument("symbol")
@click.argument("number_of_shares")
@click.argument("purchase_price")
def create(symbol, number_of_shares, purchase_price):
    """
    Create a new stock and add it to the database
    """
    stock = Stock(symbol, number_of_shares, purchase_price)
    database.session.add(stock)
    database.session.commit()


# -----------------
# Request Callbacks
# -----------------
@stocks_blueprint.before_request
def stocks_before_request():
    current_app.logger.info(
        "Calling before_request() for the stocks blueprint..."
    )


@stocks_blueprint.after_request
def stocks_after_request(response):
    current_app.logger.info(
        "Calling after_request() for the stocks blueprint..."
    )
    return response


@stocks_blueprint.teardown_request
def stocks_teardown_request(error=None):
    current_app.logger.info(
        "Calling teardown_request() for the stocks blueprint..."
    )


# --------------
# Helper Classes
# --------------
class StockModel(BaseModel):
    """Class for parsing new stock data from a form."""

    stock_symbol: str
    number_of_shares: int
    purchase_price: float

    @validator("stock_symbol")
    def stock_symbol_check(cls, value):
        if not value.isalpha() or len(value) > 5:
            raise ValueError("Stock symbol must be 1-5 characters")
        return value.upper()


def email_confirmation_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.email_confirmed:
            flash(
                "Email address not confirmed. Please check your email to confirm your email address, or use the link below to resend the email confirmation link.",
                "warning",
            )
            return redirect(url_for("users.user_profile"))
        return f(*args, **kwargs)

    return decorated_function


# ------
# Routes
# ------
@stocks_blueprint.route("/")
def index():
    current_app.logger.info("Calling the index() function.")
    return render_template("stocks/index.html")


@stocks_blueprint.route("/add_stock", methods=["GET", "POST"])
@login_required
@email_confirmation_required
def add_stock():
    if request.method == "POST":
        # print form data to console
        for key, value in request.form.items():
            print(f"{key}: {value}")

        try:
            stock_data = StockModel(
                stock_symbol=request.form["stock_symbol"],
                number_of_shares=request.form["number_of_shares"],
                purchase_price=request.form["purchase_price"],
            )
            print(stock_data)

            # save form data to the database
            new_stock = Stock(
                stock_data.stock_symbol,
                stock_data.number_of_shares,
                stock_data.purchase_price,
            )
            database.session.add(new_stock)
            database.session.commit()

            flash(
                f"Added new stock ({stock_data.stock_symbol})!",
                category="success",
            )
            current_app.logger.info(
                f"Added new stock ({stock_data.stock_symbol})!"
            )

            return redirect(url_for("stocks.list_stocks"))
        except ValidationError as e:
            print(e)

    return render_template("stocks/add_stock.html")


@stocks_blueprint.route("/stocks/")
@login_required
@email_confirmation_required
def list_stocks():
    stocks = Stock.query.order_by(Stock.id).all()
    return render_template("stocks/stocks.html", stocks=stocks)
