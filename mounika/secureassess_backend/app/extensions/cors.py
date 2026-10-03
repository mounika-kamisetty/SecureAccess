"""
SecureAssess — CORS Extension.

Configures Cross-Origin Resource Sharing from environment.
"""

from flask_cors import CORS


def init_cors(app):
    """Apply CORS with the origins specified in config."""
    CORS(
        app,
        origins=app.config["CORS_ORIGINS"],
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    )
