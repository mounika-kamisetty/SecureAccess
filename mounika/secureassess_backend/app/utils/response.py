"""
SecureAssess — Standardised JSON Response Helpers.

Every API response follows a consistent envelope:
{
    "success": true/false,
    "message": "...",
    "data": { ... }          // optional
    "error_code": "..."      // only on errors
}
"""

from flask import jsonify


def success_response(message: str, data=None, status_code: int = 200):
    """Return a successful JSON response."""
    body = {"success": True, "message": message}
    if data is not None:
        body["data"] = data
    return jsonify(body), status_code


def error_response(
    message: str,
    error_code: str = "ERROR",
    status_code: int = 400,
    errors: list | None = None,
):
    """Return an error JSON response. Never includes stack traces."""
    body = {
        "success": False,
        "message": message,
        "error_code": error_code,
    }
    if errors:
        body["errors"] = errors
    return jsonify(body), status_code


def created_response(message: str, data=None):
    return success_response(message, data, 201)


def not_found_response(message: str = "Resource not found"):
    return error_response(message, "NOT_FOUND", 404)


def forbidden_response(message: str = "Access denied"):
    return error_response(message, "FORBIDDEN", 403)


def unauthorized_response(message: str = "Authentication required"):
    return error_response(message, "UNAUTHORIZED", 401)


def conflict_response(message: str = "Resource already exists"):
    return error_response(message, "CONFLICT", 409)


def validation_error_response(message: str = "Validation error", errors=None):
    return error_response(message, "VALIDATION_ERROR", 422, errors)


def rate_limit_response(message: str = "Too many requests"):
    return error_response(message, "RATE_LIMIT_EXCEEDED", 429)
