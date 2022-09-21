from datetime import date, datetime
from functools import wraps

import click
from flask import (
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required
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
                current_user.id,
                datetime.fromisoformat(request.form["purchase_date"]),
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
    stocks = (
        Stock.query.order_by(Stock.id).filter_by(user_id=current_user.id).all()
    )
    current_account_value = 0.0
    for stock in stocks:
        stock.get_stock_data()
        if stock.current_price == 0.0:
            flash(
                (
                    f"API communication issue with retrieving "
                    f"the current stock price ({stock.stock_symbol})!"
                ),
                "error",
            )
        database.session.add(stock)
        current_account_value += stock.get_stock_position_value()

    database.session.commit()
    return render_template(
        "stocks/stocks.html",
        stocks=stocks,
        value=round(current_account_value, 2),
    )


@stocks_blueprint.route("/chartjs_demo1")
def chartjs_demo1():
    return render_template("stocks/chartjs_demo1.html")


@stocks_blueprint.route("/chartjs_demo2")
def chartjs_demo2():
    title = "Monthly Data"
    labels = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
    ]
    values = [10.3, 9.2, 8.7, 7.1, 6.0, 4.4, 7.6, 8.9]
    return render_template(
        "stocks/chartjs_demo2.html", values=values, labels=labels, title=title
    )


@stocks_blueprint.route("/chartjs_demo3")
def chartjs_demo3():
    title = "Daily Prices"
    labels = [
        datetime(2020, 2, 10),
        datetime(2020, 2, 11),
        datetime(2020, 2, 12),
        datetime(2020, 2, 13),
        datetime(2020, 2, 14),
        datetime(2020, 2, 17),
        datetime(2020, 2, 18),
        datetime(2020, 2, 19),
    ]
    values = [10.3, 9.2, 8.7, 7.1, 6.0, 4.4, 7.6, 8.9]
    return render_template(
        "stocks/chartjs_demo3.html", values=values, labels=labels, title=title
    )


@stocks_blueprint.route("/stocks/<id>")
@login_required
@email_confirmation_required
def stock_details(id):
    stock = Stock.query.filter_by(id=id).first_or_404()

    if stock.user_id != current_user.id:
        abort(403)

    title, labels, values = stock.get_weekly_stock_data()
    return render_template(
        "stocks/stock_details.html",
        stock=stock,
        title=title,
        labels=labels,
        values=values,
    )
