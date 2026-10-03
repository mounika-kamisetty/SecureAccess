"""
SecureAssess — Flask Application Factory.

Creates and configures the Flask app instance.
"""

import click
from flask import Flask

from app.config import get_config
from app.extensions.mongo import mongo
from app.extensions.jwt_manager import jwt_manager
from app.extensions.cors import init_cors
from app.middleware.error_handler import register_error_handlers
from app.api.routes import register_routes
from app.utils.logger import setup_logger


def create_app(config_class=None):
    """
    Application factory.

    Args:
        config_class: Optional config class override (used in testing).
    """
    app = Flask(__name__)

    # --- Load configuration ---
    if config_class:
        app.config.from_object(config_class)
    else:
        app.config.from_object(get_config())

    # --- Security headers ---
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Cache-Control"] = "no-store"
        response.headers["Pragma"] = "no-cache"
        return response

    # --- Initialise extensions ---
    mongo.init_app(app)
    # Initialize auth
    jwt_manager.init_app(app)
    init_cors(app)

    # --- Register error handlers ---
    register_error_handlers(app)

    # --- Register routes ---
    register_routes(app)

    # --- Setup logging ---
    setup_logger(app)

    # --- CLI: Seed admin user ---
    @app.cli.command("seed-admin")
    def seed_admin():
        """Create the first admin user from .env variables."""
        from app.models.user_model import find_user_by_email, create_user
        from app.utils.security import normalize_email

        email = normalize_email(app.config["ADMIN_EMAIL"])
        if find_user_by_email(email):
            click.echo(f"Admin user '{email}' already exists.")
            return

        user = create_user(
            name=app.config["ADMIN_NAME"],
            email=email,
            password=app.config["ADMIN_PASSWORD"],
            role="admin",
        )
        click.echo(f"Admin user created: {user['email']} (ID: {user['id']})")

    return app
