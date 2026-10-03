"""
SecureAssess — Authentication Middleware.

Provides the @jwt_required decorator that:
1. Validates the Bearer token using Flask-JWT-Extended.
2. Attaches user identity (user_id, role) to Flask's g object.
"""

from functools import wraps

from flask import g
from flask_jwt_extended import verify_jwt_in_request, get_jwt, get_jwt_identity


def jwt_required(f):
    """
    Decorator that protects an endpoint with JWT authentication.

    After successful verification, ``g.current_user`` is set to::

        {"user_id": "...", "role": "...", "jti": "..."}
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        # flask_jwt_extended handles token extraction and validation
        verify_jwt_in_request()
        
        claims = get_jwt()

        # Attach identity to the request context to maintain backwards compatibility
        # with our existing routes and role_middleware
        g.current_user = {
            "user_id": get_jwt_identity(),
            "role": claims.get("role"),
            "jti": claims.get("jti", ""),
        }

        return f(*args, **kwargs)

    return decorated
