"""
The users blueprint handles user management for this application.
Specifically, it allows for new users to register and log in/out of the application.
"""
from flask import Blueprint

users_blueprint = Blueprint("users", __name__, template_folder="templates")

from . import routes
