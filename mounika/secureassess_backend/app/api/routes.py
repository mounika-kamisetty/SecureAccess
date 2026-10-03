"""
SecureAssess — Central API Blueprint Registration.

All route blueprints are collected here and registered under /api/v1.
"""

from flask import Flask, Blueprint

from app.routes.auth_routes import auth_bp
from app.routes.user_routes import user_bp
from app.routes.exam_routes import exam_bp
from app.routes.attempt_routes import attempt_bp
from app.routes.event_routes import event_bp
from app.routes.admin_routes import admin_bp
from app.routes.health_routes import health_bp


def register_routes(app: Flask):
    """Register all API v1 blueprints under /api/v1."""
    api_v1 = Blueprint("api_v1", __name__, url_prefix="/api/v1")

    api_v1.register_blueprint(auth_bp)
    api_v1.register_blueprint(user_bp)
    api_v1.register_blueprint(exam_bp)
    api_v1.register_blueprint(attempt_bp)
    api_v1.register_blueprint(event_bp)
    api_v1.register_blueprint(admin_bp)
    api_v1.register_blueprint(health_bp)

    app.register_blueprint(api_v1)
