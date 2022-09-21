from flask import current_app
from itsdangerous import URLSafeTimedSerializer

from project import mail
from project.models import User


def test_get_registration_page(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the 'users/register' page is requested (GET)
    THEN check if response is valid
    """
    response = test_client.get("/users/register")
    assert response.status_code == 200
    assert b"Flask Stock Portfolio App" in response.data
    assert b"User Registration" in response.data
    assert b"Email" in response.data
    assert b"Password" in response.data


def test_valid_registration(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/users/register' page is posted (POST) with valid data
    THEN check if response is valid, user is registered, and email was queued up to send
    """
    with mail.record_messages() as outbox:
        response = test_client.post(
            "/users/register",
            data={
                "email": "user@gmail.com",
                "password": "FlaskIsAwesome123",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Thanks for registering, user@gmail.com!" in response.data
        assert b"Flask Stock Portfolio App" in response.data
        assert len(outbox) == 1
        assert (
            outbox[0].subject
            == "Flask Stock Portfolio App - Confirm Your Email Address"
        )
        assert outbox[0].sender == "test.stockportfolio@gmail.com"
        assert outbox[0].recipients[0] == "user@gmail.com"
        assert "http://localhost/users/confirm" in outbox[0].html


def test_invalid_registration_missing_pasword(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the 'users/register' page is posted (POST) with invalid data (missing password)
    THEN check if error message is returned to the user
    """
    response = test_client.post(
        "/users/register",
        data={
            "email": "user2@gmail.com",
            "password": "",  # missing password
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Thanks for registering, user2@gmail.com!" not in response.data
    assert b"Flask Stock Portfolio App" in response.data
    assert b"[This field is required.]" in response.data


def test_invalid_registration_duplicate_user(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the 'users/register' page is posted (POST) with email address for an existing user
    THEN check if error message is returned to the user
    """
    test_client.post(
        "/users/register",
        data={
            "email": "user@hotmail.com",
            "password": "FlaskIsStillGreat!",
        },
        follow_redirects=True,
    )
    response = test_client.post(
        "/users/register",
        data={
            "email": "user@hotmail.com",
            "password": "FlaskIsStillGreat!",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Thanks for registering, user2@gmail.com!" not in response.data
    assert b"Flask Stock Portfolio App" in response.data
    assert b"ERROR! Email (user@hotmail.com) already exists." in response.data


def test_get_login_page(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/users/login' page is requested (GET)
    THEN check if response is valid
    """
    response = test_client.get("/users/login")
    assert response.status_code == 200
    assert b"Login" in response.data
    assert b"Email" in response.data
    assert b"Password" in response.data
    assert b"Login" in response.data
    assert b"Forgot your password?" in response.data


def test_valid_login_and_logout(
    test_client, confirm_email_default_user_not_logged_in
):
    """
    GIVEN a Flask application configured for testing
        and the user email has been confirmed
    WHEN the '/users/login' page is posted to (POST) with valid credentials
    THEN check if response is valid
    """
    response = test_client.post(
        "/users/login",
        data={
            "email": "user@gmail.com",
            "password": "FlaskIsAwesome123",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Thanks for logging in, user@gmail.com!" in response.data
    assert b"Flask Stock Portfolio App" in response.data
    assert b"Please log in to access this page." not in response.data

    """
    GIVEN a Flask application configured for testing
    WHEN the 'users/logout' page is requested (GET) for a logged in user
    THEN check if response is valid
    """
    response = test_client.get("/users/logout", follow_redirects=True)
    assert response.status_code == 200
    assert b"Goodbye!" in response.data
    assert b"Flask Stock Portfolio App" in response.data
    assert b"Please log in to access this page." not in response.data


def test_valid_login_not_confirmed_logout(test_client, register_default_user):
    """
    GIVEN a Flask application configured for testing
        and the user email has NOT been confirmed
    WHEN the '/users/login' page is posted to (POST) with valid credentials
    THEN check if response is valid
        and warning message is displayed to the user
    """
    response = test_client.post(
        "/users/login",
        data={
            "email": "user@gmail.com",
            "password": "FlaskIsAwesome123",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert (
        b"Email address not confirmed. Please check your email to confirm your email address, or use the link below to resend the email confirmation link."
        in response.data
    )
    assert b"Thanks for logging in, user@gmail.com!" in response.data
    assert b"Flask Stock Portfolio App" in response.data
    assert b"Please log in to access this page." not in response.data

    """
    GIVEN a Flask application configured for testing
    WHEN the 'users/logout' page is requested (GET) for a logged in user
    THEN check if response is valid
    """
    response = test_client.get("/users/logout", follow_redirects=True)
    assert response.status_code == 200
    assert b"Goodbye!" in response.data
    assert b"Flask Stock Portfolio App" in response.data
    assert b"Please log in to access this page." not in response.data


def test_invalid_login(test_client, register_default_user):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/users/login' page is posted to (POST) with invalid credentials (incorrect password)
    THEN check if error message is returned to user
    """
    response = test_client.post(
        "/users/login",
        data={"email": "user@gmail.com", "password": "FlaskIsNotAwesome"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"ERROR! Incorrect login credentials." in response.data
    assert b"Flask Stock Portfolio App" in response.data


def test_valid_login_when_logged_in_already(test_client, log_in_default_user):
    """
    GIVEN a Flask application configured for testing and default user logged in
    WHEN the "/users/login" page is posted to (POST) with valid credentials for the default user
    THEN check a warning is displayed to the user (already logged in)
    """
    response = test_client.post(
        "/users/login",
        data={"email": "user@gmail.com", "password": "FlaskIsAwesome123"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Already logged in!" in response.data
    assert b"Flask Stock Portfolio App" in response.data


def test_invalid_logout(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/users/logout' page is posted to (POST)
    THEN check that a 405 error is returned
    """
    response = test_client.post("/users/logout", follow_redirects=True)
    assert response.status_code == 405
    assert b"Goodbye!" not in response.data
    assert b"Flask Stock Portfolio App" in response.data
    assert b"Method Not Allowed" in response.data


def test_invalid_logout_not_logged_in(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/users/logout' page is requested (GET) when user is not logged in
    THEN check that user is redirected to the login page
    """
    # ensure there are no logged in users
    test_client.get("/users/logout", follow_redirects=True)

    response = test_client.get("/users/logout", follow_redirects=True)
    assert response.status_code == 200
    assert b"Goodbye!" not in response.data
    assert b"Flask Stock Portfolio App" in response.data
    assert b"Login" in response.data
    assert b"Please log in to access this page." in response.data


def test_user_profile_logged_in(test_client, log_in_default_user):
    """
    GIVEN a Flask application configured for testing and default user is logged in
    WHEN the '/users/profile' page is requested (GET)
    THEN check that the profile for the current user is displayed
    """
    response = test_client.get("/users/profile")
    assert response.status_code == 200
    assert b"Flask Stock Portfolio App" in response.data
    assert b"User Profile" in response.data
    assert b"Email: user@gmail.com" in response.data
    assert b"Account Statistics" in response.data
    assert b"Joined on" in response.data
    assert b"Email address has not been confirmed!" in response.data
    assert b"Email address confirmed on" not in response.data
    assert b"Account Actions" in response.data
    assert b"Change Password" in response.data
    assert b"Resend Email Confirmation" in response.data


def test_user_profile_logged_in_email_confirmed(
    test_client, confirm_email_default_user_logged_in
):
    """
    GIVEN a Flask application configured for testing and default user is logged in
        and their email address is confirmed
    WHEN the '/users/profile' page is requested (GET)
    THEN check that the profile for the current user is displayed
    """
    response = test_client.get("/users/profile")
    assert response.status_code == 200
    assert b"Flask Stock Portfolio App" in response.data
    assert b"User Profile" in response.data
    assert b"Email: user@gmail.com" in response.data
    assert b"Account Statistics" in response.data
    assert b"Joined on" in response.data
    assert b"Email address has not been confirmed!" not in response.data
    assert b"Email address confirmed on Friday, July 08, 2022" in response.data
    assert b"Account Actions" in response.data
    assert b"Change Password" in response.data
    assert b"Resend Email Confirmation" not in response.data


def test_user_profile_not_logged_in(test_client):
    """
    GIVEN a Flask application configured for testing and default user is NOT logged in
    WHEN the '/users/profile' page is requested (GET)
    THEN check that the user is redirected to the login page
    """
    response = test_client.get("/users/profile", follow_redirects=True)
    assert response.status_code == 200
    assert b"Flask Stock Portfolio App" in response.data
    assert b"User Profile" not in response.data
    assert b"Email: user@gmail.com" not in response.data
    assert b"Please log in to access this page." in response.data


def test_navigation_bar_logged_in(test_client, log_in_default_user):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/' page is requested (GET) when user is logged in
    THEN check that the 'List Stocks', 'Add Stock', 'Profile' and 'Logout' links are present
    """
    response = test_client.get("/")
    assert response.status_code == 200
    assert b"Flask Stock Portfolio App" in response.data
    assert b"Welcome to the" in response.data
    assert b"Flask Stock Portfolio App!" in response.data
    assert b"List Stocks" in response.data
    assert b"Add Stock" in response.data
    assert b"Profile" in response.data
    assert b"Logout" in response.data
    assert b"Register" not in response.data
    assert b"Login" not in response.data


def test_navigation_bar_not_logged_in(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/' page is requested (GET) when user is not logged in
    THEN check that the 'Register' and 'Login' links are present
    """
    response = test_client.get("/")
    assert response.status_code == 200
    assert b"Flask Stock Portfolio App" in response.data
    assert b"Welcome to the" in response.data
    assert b"Flask Stock Portfolio App!" in response.data
    assert b"Register" in response.data
    assert b"Login" in response.data
    assert b"List Stocks" not in response.data
    assert b"Add Stock" not in response.data
    assert b"Profile" not in response.data
    assert b"Logout" not in response.data


def test_login_with_next_valid_path(test_client, register_default_user):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/users/login?next=%2Fusers%2profile' page is posted to (POST) with a valid user login
    THEN check that the user is redirected to the user profile page
    """
    response = test_client.post(
        "/users/login?next=%2Fusers%2Fprofile",
        data={"email": "user@gmail.com", "password": "FlaskIsAwesome123"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Flask Stock Portfolio App" in response.data
    assert b"User Profile" in response.data
    assert b"Email: user@gmail.com" in response.data

    # log out the user
    test_client.get("/users/logout", follow_redirects=True)


def test_login_with_next_invalid_path(
    test_client, confirm_email_default_user_not_logged_in
):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/users/login?next=http://www.badsite.com' page is posted to (POST) with a valid user login
    THEN check that a 400 (Bad Request) error is returned
    """
    response = test_client.post(
        "/users/login?next=http://www.badsite.com",
        data={"email": "user@gmail.com", "password": "FlaskIsAwesome123"},
        follow_redirects=True,
    )
    assert response.status_code == 400
    assert b"User Profile" not in response.data
    assert b"Email: user@gmail.com" not in response.data


def test_confirm_email_valid(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/users/confirm/<token>' page is requested (GET) with valid data
    THEN check that the user's email is marked as confirmed
    """
    # create the unique token for confirming a user's email address
    confirm_serializer = URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"]
    )
    token = confirm_serializer.dumps(
        "user@gmail.com", salt="email-confirmation-salt"
    )

    response = test_client.get(
        f"/users/confirm/{token}", follow_redirects=True
    )
    assert response.status_code == 200
    assert b"Thank you for confirming your email address!" in response.data
    user = User.query.filter_by(email="user@gmail.com").first()
    assert user.email_confirmed


def test_confirm_email_already_confirmed(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/users/confirm/<token>' page is requested (GET) with valid data
        but the user's email is already confirmed
    THEN check that the user's email is marked as confirmed
    """
    # create the unique token for confirming a user's email address
    confirm_serializer = URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"]
    )
    token = confirm_serializer.dumps(
        "user@gmail.com", salt="email-confirmation-salt"
    )

    # process a valid confirmation link for a user that has already confirmed email address
    response = test_client.get(
        f"/users/confirm/{token}", follow_redirects=True
    )
    assert response.status_code == 200
    assert b"Account already confirmed. Please login." in response.data
    user = User.query.filter_by(email="user@gmail.com").first()
    assert user.email_confirmed


def test_confirm_email_invalid(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/users/confirm/<token>' page is requested (GET) with invalid data
    THEN check that the link was not accepted
    """
    response = test_client.get(
        "/users/confirm/bad_confirmation_link", follow_redirects=True
    )
    assert response.status_code == 200
    assert b"The confirmation link is invalid or has expired." in response.data


def test_set_password(new_user):
    """
    GIVEN a User model
    WHEN the user's password is changed
    THEN check that the password has successfully been changed
    """
    new_user.set_password("FlaskIsStillAwesome456")
    assert new_user.email == "user@gmail.com"
    assert new_user.password_hashed != "FlaskIsStillAwesome456"
    assert new_user.is_password_correct("FlaskIsStillAwesome456")


def test_get_password_reset_via_email_page(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/users/password_reset_via_email` page is requested (GET)
    THEN check that the page is successfully returned
    """
    response = test_client.get(
        "/users/password_reset_via_email", follow_redirects=True
    )
    assert response.status_code == 200
    assert b"Password Reset via Email" in response.data
    assert b"Email" in response.data
    assert b"Submit" in response.data


def test_post_password_reset_via_email_valid(
    test_client, confirm_email_default_user_logged_in
):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/users/password_reset_via_email` page is posted to (POST)
        with a valid email address
    THEN check that an email was queued up to send
    """
    with mail.record_messages() as outbox:
        response = test_client.post(
            "/users/password_reset_via_email",
            data={"email": "user@gmail.com"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert (
            b"Please check your email for a password reset link."
            in response.data
        )
        assert len(outbox) == 1
        assert (
            outbox[0].subject
            == "Flask Stock Portfolio App - Password Reset Requested"
        )
        assert outbox[0].sender == "test.stockportfolio@gmail.com"
        assert outbox[0].recipients[0] == "user@gmail.com"
        assert "Questions? Comments?" in outbox[0].html
        assert "test.stockportfolio@gmail.com" in outbox[0].html
        assert (
            "http://localhost/users/password_reset_via_token" in outbox[0].html
        )


def test_post_password_reset_via_email_invalid(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/users/password_reset_via_email` page is posted to (POST)
        with an invalid email address
    THEN check that an error message was flashed
    """
    with mail.record_messages() as outbox:
        response = test_client.post(
            "/users/password_reset_via_email",
            data={"email": "notuser@gmail.com"},  # invalid email address
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert len(outbox) == 0
        assert b"ERROR! Invalid email address!" in response.data


def test_post_password_reset_via_email_not_confirmed(
    test_client, log_in_default_user
):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/users/password_reset_via_email` page is posted to (POST)
        with an email address that has not been confirmed
    THEN check that an error message was flashed
    """
    with mail.record_messages() as outbox:
        response = test_client.post(
            "/users/password_reset_via_email",
            data={"email": "user@gmail.com"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert len(outbox) == 0
        assert (
            b"Your email address must be confirmed before attempting a password reset."
            in response.data
        )


def test_get_password_reset_valid_token(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/users/password_reset_via_token/<token>' page is requested (GET)
        with a valid token
    THEN check if the password reset form is successfully returned
    """
    password_reset_serializer = URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"]
    )
    token = password_reset_serializer.dumps(
        "user@gmail.com", salt="password-reset-salt"
    )
    response = test_client.get(
        f"/users/password_reset_via_token/{token}",
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Password Reset" in response.data
    assert b"New Password" in response.data
    assert b"Submit" in response.data


def test_get_password_reset_invalid_token(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/users/password_reset_via_token/<token>' page is requested (GET)
        with an invalid token
    THEN check if an error message is displayed
    """
    token = "invalid_token"

    response = test_client.get(
        f"/users/password_reset_via_token/{token}",
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Password Reset" not in response.data
    assert (
        b"The password reset link is invalid or has expired." in response.data
    )


def test_post_password_reset_valid_token(
    test_client, afterwards_reset_default_user_password
):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/users/password_reset_via_token/<token>' page is posted to (POST)
        with a valid token
    THEN check that the password provided is processed
    """
    password_reset_serializer = URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"]
    )
    token = password_reset_serializer.dumps(
        "user@gmail.com", salt="password-reset-salt"
    )

    response = test_client.post(
        f"/users/password_reset_via_token/{token}",
        data={"password": "FlaskIsDaBest789"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Your password has been updated!" in response.data


def test_post_password_reset_invalid_token(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/users/password_reset_via_token/<token>' page is posted to (POST)
        with an invalid token
    THEN check that the password provided is not processed
    """
    token = "invalid_token"

    response = test_client.post(
        f"/users/password_reset_via_token/{token}",
        data={"password": "FlaskIsStillGreat987"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Your password has been updated!" not in response.data
    assert (
        b"The password reset link is invalid or has expired." in response.data
    )


def test_get_change_password_logged_in(test_client, log_in_default_user):
    """
    GIVEN a Flask application configured for testing with the user logged in
    WHEN the '/users/change_password` page is requested (GET)
    THEN check that the page is retrieved successfully
    """
    response = test_client.get("/users/change_password", follow_redirects=True)
    assert response.status_code == 200
    assert b"Change Password" in response.data
    assert b"Current Password" in response.data
    assert b"New Password" in response.data


def test_get_change_password_not_logged_in(test_client):
    """
    GIVEN a Flask application configured for testing with the user NOT logged in
    WHEN the '/users/change_password` page is requested (GET)
    THEN check that an error message is returned to the user
    """
    response = test_client.get("/users/change_password", follow_redirects=True)
    assert response.status_code == 200
    assert b"Please log in to access this page." in response.data
    assert b"Change Password" not in response.data


def test_post_change_password_logged_in_valid_current_password(
    test_client, log_in_default_user, afterwards_reset_default_user_password
):
    """
    GIVEN a Flask application configured for testing with the user logged in
    WHEN the '/users/change_password` page is posted to (POST)
        with the correct current password
    THEN check that the password is updated successfully
    """
    response = test_client.post(
        "/users/change_password",
        data={
            "current_password": "FlaskIsAwesome123",
            "new_password": "FlaskIsStillAwesome123",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Password has been updated!" in response.data
    user = User.query.filter_by(email="user@gmail.com").first()
    assert not user.is_password_correct("FlaskIsAwesome123")
    assert user.is_password_correct("FlaskIsStillAwesome123")


def test_post_change_password_logged_in_invalid_current_password(
    test_client, log_in_default_user
):
    """
    GIVEN a Flask application configured for testing with the user logged in
    WHEN the '/users/change_password` page is posted to (POST)
        with an incorrect current password
    THEN check that an error message is returned to the user
    """
    response = test_client.post(
        "/users/change_password",
        data={
            "current_password": "FlaskIsNotAwesome123",
            "new_password": "FlaskIsStillAwesome123",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Password has been updated!" not in response.data
    assert b"ERROR! Incorrect user credentials!" in response.data


def test_post_change_password_not_logged_in(test_client):
    """
    GIVEN a Flask application configured for testing with the user NOT logged in
    WHEN the '/users/change_password` page is posted to (POST)
    THEN check that an error message is returned to the user
    """
    response = test_client.post(
        "/users/change_password",
        data={
            "current_password": "FlaskIsAwesome123",
            "new_password": "FlaskIsStillAwesome123",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Please log in to access this page." in response.data
    assert b"Password has been updated!" not in response.data


def test_get_change_email_logged_in(test_client, log_in_default_user):
    """
    GIVEN a Flask application configured for testing with the user logged in
    WHEN the '/users/change_email` page is requested (GET)
    THEN check that the page is retrieved successfully
    """
    response = test_client.get("/users/change_email", follow_redirects=True)
    assert response.status_code == 200
    assert b"Change Email" in response.data
    assert b"New Email" in response.data


def test_get_change_email_not_logged_in(test_client):
    """
    GIVEN a Flask application configured for testing with the user NOT logged in
    WHEN the '/users/change_email` page is requested (GET)
    THEN check that an error message is returned to the user
    """
    response = test_client.get("/users/change_email", follow_redirects=True)
    assert response.status_code == 200
    assert b"Please log in to access this page." in response.data
    assert b"Change Email" not in response.data


def test_post_change_email_logged_in_valid_email(
    test_client, log_in_default_user, afterwards_reset_default_user_email
):
    """
    GIVEN a Flask application configured for testing with the user logged in
    WHEN the '/users/change_email` page is posted to (POST)
        with a valid new email address
    THEN check that the user's email address is updated successfully
        and that an email was queued up to send
    """
    with mail.record_messages() as outbox:
        response = test_client.post(
            "/users/change_email",
            data={"new_email": "user.edited@gmail.com"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Email address has been updated!" in response.data
        assert (
            b"Email sent to confirm your email address. Please check your email!"
            in response.data
        )
        assert len(outbox) == 1
        assert (
            outbox[0].subject
            == "Flask Stock Portfolio App - Confirm Your Email Address"
        )
        assert outbox[0].sender == "test.stockportfolio@gmail.com"
        assert outbox[0].recipients[0] == "user.edited@gmail.com"
        assert "http://localhost/users/confirm/" in outbox[0].html


def test_post_change_email_logged_in_invalid_email(
    test_client, log_in_default_user
):
    """
    GIVEN a Flask application configured for testing with the user logged in
    WHEN the '/users/change_email` page is posted to (POST)
        with an invalid new email address (already exists)
    THEN check that an error is returned to the user
        and that an email was not queued up to send
    """
    with mail.record_messages() as outbox:
        response = test_client.post(
            "/users/change_email",
            data={"new_email": "user@gmail.com"},  # email already exists
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert (
            b"ERROR! A user with the provided email already exists!"
            in response.data
        )
        assert (
            b"Email sent to confirm your email address. Please check your email!"
            not in response.data
        )
        assert len(outbox) == 0


def test_post_change_email_not_logged_in(test_client):
    """
    GIVEN a Flask application configured for testing with the user NOT logged in
    WHEN the '/users/change_email` page is posted to (POST)
    THEN check that an error message is returned to the user
    """
    response = test_client.post(
        "/users/change_email",
        data={"new_email": "user.edited@gmail.com"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Please log in to access this page." in response.data
    assert (
        b"Email sent to confirm your email address. Please check your email!"
        not in response.data
    )
    # assert b"Email address has been updated!" not in response.data


def test_get_resend_email_confirmation_logged_in(
    test_client, log_in_default_user
):
    """
    GIVEN a Flask application configured for testing with the user logged in
    WHEN the '/users/resend_email_confirmation` page is requested (GET)
    THEN check that an email was queued up to send
    """
    with mail.record_messages() as outbox:
        response = test_client.get(
            "/users/resend_email_confirmation", follow_redirects=True
        )
        assert response.status_code == 200
        assert (
            b"Email sent to confirm your email address. Please check your email!"
            in response.data
        )
        assert len(outbox) == 1
        assert (
            outbox[0].subject
            == "Flask Stock Portfolio App - Confirm Your Email Address"
        )
        assert outbox[0].sender == "test.stockportfolio@gmail.com"
        assert outbox[0].recipients[0] == "user@gmail.com"
        assert "http://localhost/users/confirm/" in outbox[0].html


def test_get_resend_email_confirmation_not_logged_in(test_client):
    """
    GIVEN a Flask application configured for testing with the user NOT logged in
    WHEN the '/users/resend_email_confirmation` page is requested (GET)
    THEN check that an email was not queued up to send
    """
    with mail.record_messages() as outbox:
        response = test_client.get(
            "/users/resend_email_confirmation", follow_redirects=True
        )
        assert response.status_code == 200
        assert (
            b"Email sent to confirm your email address. Please check your email!"
            not in response.data
        )
        assert len(outbox) == 0
        assert b"Please log in to access this page." in response.data
