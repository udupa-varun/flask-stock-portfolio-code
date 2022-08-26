from flask import abort, flash, render_template

from . import users_blueprint


@users_blueprint.errorhandler(403)
def page_forbidden(e):
    return render_template("users/403.html"), 403


# ------
# Routes
# ------
@users_blueprint.route("/about")
def about():
    flash("Thanks for learning about this site!", category="info")
    return render_template("users/about.html", company_name="TestDriven.io")


@users_blueprint.route("/admin")
def admin():
    abort(403)
