from datetime import datetime
from threading import Thread
from urllib.parse import urlparse

from flask import (
    abort,
    copy_current_request_context,
    current_app,
    escape,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import (
    current_user,
    fresh_login_required,
    login_required,
    login_user,
    logout_user,
)
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
from itsdangerous.exc import BadSignature
from sqlalchemy.exc import IntegrityError

from project import database, mail
from project.models import User
from project.users.forms import (
    ChangeEmailForm,
    ChangePasswordForm,
    EmailForm,
    LoginForm,
    PasswordForm,
    RegistrationForm,
)

from . import users_blueprint

# ----------------
# Helper Functions
# ----------------


def generate_confirmation_email(user_email):
    confirm_serializer = URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"]
    )

    confirm_url = url_for(
        "users.confirm_email",
        token=confirm_serializer.dumps(
            user_email, salt="email-confirmation-salt"
        ),
        _external=True,
    )

    return Message(
        subject="Flask Stock Portfolio App - Confirm Your Email Address",
        html=render_template(
            "users/email_confirmation.html", confirm_url=confirm_url
        ),
        recipients=[user_email],
    )


def generate_password_reset_email(user_email):
    password_reset_serializer = URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"]
    )

    password_reset_url = url_for(
        "users.process_password_reset_token",
        token=password_reset_serializer.dumps(
            user_email, salt="password-reset-salt"
        ),
        _external=True,
    )

    return Message(
        subject="Flask Stock Portfolio App - Password Reset Requested",
        html=render_template(
            "users/email_password_reset.html",
            password_reset_url=password_reset_url,
        ),
        recipients=[user_email],
    )


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


@users_blueprint.route("/hello/<path:message>")
def print_path(message):
    return f"<h1>Path provided: {escape(message)}!</h1>"


@users_blueprint.route("/logout", methods=["GET"])
@login_required
def logout():
    current_app.logger.info(f"Logged out user: {current_user.email}")
    logout_user()
    flash("Goodbye!")
    return redirect(url_for("stocks.index"))


@users_blueprint.route("/login", methods=["GET", "POST"])
def login():
    # if user is already logged in, don't let them login again
    if current_user.is_authenticated:
        flash("Already logged in!")
        current_app.logger.info(
            f"Duplicate login attempt by user: {current_user.email}"
        )
        return redirect(url_for("stocks.index"))

    form = LoginForm()

    if request.method == "POST":
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and user.is_password_correct(form.password.data):
                # User credentials have been validated, so log them in
                login_user(user, remember=form.remember_me.data)
                flash(f"Thanks for logging in, {current_user.email}!")
                current_app.logger.info(
                    f"Logged in user: {current_user.email}"
                )

                # if the user email has not been confirmed, flash a reminder
                if not user.email_confirmed:
                    flash(
                        "Email address not confirmed. Please check your email to confirm your email address, or use the link below to resend the email confirmation link.",
                        "warning",
                    )
                    return redirect(url_for("users.user_profile"))

                # if the next URL is not specified, redirect to the user profile
                if not request.args.get("next"):
                    return redirect(url_for("users.user_profile"))

                # process the query to determine if user should be redirected after login
                next_url = request.args.get("next")
                if (
                    urlparse(next_url).scheme != ""
                    or urlparse(next_url).netloc != ""
                ):
                    current_app.logger.info(
                        f"Invalid next path in login request: {next_url}"
                    )
                    logout_user()
                    return abort(400)

                current_app.logger.info(
                    f"Redirecting after valid login to: {next_url}"
                )
                return redirect(next_url)

                return redirect(url_for("stocks.index"))

        flash("ERROR! Incorrect login credentials.", "error")
    return render_template("users/login.html", form=form)


@users_blueprint.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()

    if request.method == "POST":
        if form.validate_on_submit():
            try:
                new_user = User(form.email.data, form.password.data)
                database.session.add(new_user)
                database.session.commit()
                flash(
                    f"Thanks for registering, {new_user.email}! Please check your email to confirm your email address.",
                    "success",
                )
                current_app.logger.info(
                    f"Registered new user: {form.email.data}!"
                )

                @copy_current_request_context
                def send_email(message):
                    with current_app.app_context():
                        mail.send(message)

                # send an email to the user confirming the new registration
                msg = generate_confirmation_email(form.email.data)
                email_thread = Thread(target=send_email, args=[msg])
                email_thread.start()

                return redirect(url_for("users.login"))
            except IntegrityError:
                database.session.rollback()
                flash(
                    f"ERROR! Email ({form.email.data}) already exists.",
                    "error",
                )
        else:
            flash(f"Error in form data!", "error")

    return render_template("users/register.html", form=form)


@users_blueprint.route("/profile")
@login_required
def user_profile():
    return render_template("users/profile.html")


@users_blueprint.route("/confirm/<token>")
def confirm_email(token):
    try:
        confirm_serializer = URLSafeTimedSerializer(
            current_app.config["SECRET_KEY"]
        )
        email = confirm_serializer.loads(
            token, salt="email-confirmation-salt", max_age=3600
        )
    except BadSignature:
        flash("The confirmation link is invalid or has expired.", "error")
        current_app.logger.info(
            f"Invalid or expired confirmation link received from IP address: {request.remote_addr}"
        )
        return redirect(url_for("users.login"))

    user = User.query.filter_by(email=email).first()

    if user.email_confirmed:
        flash("Account already confirmed. Please login.", "info")
        current_app.logger.info(
            f"Confirmation link received for a confirmed user: {user.email}"
        )
    else:
        user.email_confirmed = True
        user.email_confirmed_on = datetime.now()
        database.session.add(user)
        database.session.commit()
        flash("Thank you for confirming your email address!", "success")
        current_app.logger.info(
            f"Email address confirmed for user: {user.email}"
        )

    return redirect(url_for("stocks.index"))


@users_blueprint.route("/password_reset_via_email", methods=["GET", "POST"])
def password_reset_via_email():
    form = EmailForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user is None:
            flash("ERROR! Invalid email address!", "error")
            return render_template(
                "users/password_reset_via_email.html", form=form
            )

        if user.email_confirmed:

            @copy_current_request_context
            def send_email(message):
                with current_app.app_context():
                    mail.send(message)

            # send a password reset email
            msg = generate_password_reset_email(form.email.data)
            email_thread = Thread(target=send_email, args=[msg])
            email_thread.start()

            flash(
                "Please check your email for a password reset link.", "success"
            )
        else:
            flash(
                "Your email address must be confirmed before attempting a password reset.",
                "error",
            )
        return redirect(url_for("users.login"))

    return render_template("users/password_reset_via_email.html", form=form)


@users_blueprint.route(
    "/password_reset_via_token/<token>", methods=["GET", "POST"]
)
def process_password_reset_token(token):
    try:
        password_reset_serializer = URLSafeTimedSerializer(
            current_app.config["SECRET_KEY"]
        )
        email = password_reset_serializer.loads(
            token, salt="password-reset-salt", max_age=3600
        )
    except BadSignature:
        flash("The password reset link is invalid or has expired.", "error")
        return redirect(url_for("users.login"))

    form = PasswordForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=email).first()

        if user is None:
            flash("Invalid email address!", "error")
            return redirect(url_for("users.login"))

        user.set_password(form.password.data)
        database.session.add(user)
        database.session.commit()
        flash("Your password has been updated!", "success")
        return redirect(url_for("users.login"))

    return render_template("users/reset_password_with_token.html", form=form)


@users_blueprint.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        if current_user.is_password_correct(form.current_password.data):
            current_user.set_password(form.new_password.data)
            database.session.add(current_user)
            database.session.commit()
            flash("Password has been updated!", "success")
            current_app.logger.info(
                f"Password updated for user {current_user.email}"
            )
            return redirect(url_for("users.user_profile"))
        else:
            flash("ERROR! Incorrect user credentials!", "error")
            current_app.logger.info(
                f"Incorrect password change for user: {current_user.email}"
            )
    return render_template("users/change_password.html", form=form)


@users_blueprint.route("/resend_email_confirmation")
@login_required
def resend_email_confirmation():
    @copy_current_request_context
    def send_email(message):
        with current_app.app_context():
            mail.send(message)

    # send an email to confirm the user's email address
    msg = generate_confirmation_email(current_user.email)
    email_thread = Thread(target=send_email, args=[msg])
    email_thread.start()

    flash(
        "Email sent to confirm your email address. Please check your email!",
        "success",
    )
    current_app.logger.info(
        f"Email re-sent to confirm email address for user: {current_user.email}"
    )
    return redirect(url_for("users.user_profile"))


@users_blueprint.route("/change_email", methods=["GET", "POST"])
@fresh_login_required
def change_email():
    form = ChangeEmailForm()

    if form.validate_on_submit():
        old_email = current_user.email
        new_email = form.new_email.data

        # check if user with new email already exists
        if User.query.filter_by(email=new_email).first() is not None:
            flash(
                "ERROR! A user with the provided email already exists!",
                "error",
            )
            current_app.logger.info(
                f"Incorrect email change for user: {old_email}"
            )
        else:
            current_user.set_email(form.new_email.data)
            database.session.add(current_user)
            database.session.commit()
            flash("Email address has been updated!", "success")
            current_app.logger.info(
                f"Email updated for user {old_email} to {current_user.email}"
            )
            return redirect(url_for("users.resend_email_confirmation"))

    return render_template("users/change_email.html", form=form)
