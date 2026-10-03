"""
SecureAssess — Role-Based Access Control Middleware.

Provides the @roles_required decorator to restrict endpoints
to specific user roles (student, examiner, admin).
"""

from functools import wraps

from flask import g

from app.utils.response import forbidden_response


def roles_required(*allowed_roles: str):
    """
    Decorator that restricts access to users whose JWT role claim
    is in *allowed_roles*.

    Must be applied **after** @jwt_required so that g.current_user exists.

    Usage::

        @jwt_required
        @roles_required("admin", "examiner")
        def create_exam():
            ...
    """

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = getattr(g, "current_user", None)
            if not user:
                return forbidden_response("Authentication context missing")

            if user["role"] not in allowed_roles:
                return forbidden_response(
                    f"Role '{user['role']}' is not authorised for this action"
                )
            return f(*args, **kwargs)

        return decorated

    return decorator
