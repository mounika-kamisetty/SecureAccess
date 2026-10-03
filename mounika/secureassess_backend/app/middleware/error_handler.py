"""
SecureAssess — Centralised Error Handlers.

Registers Flask error handlers that return consistent JSON responses
and never expose stack traces, filesystem paths, or internal details.
"""

from flask import Flask, jsonify

from app.utils.logger import get_logger


def register_error_handlers(app: Flask):
    """Attach error handlers for common HTTP status codes."""

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "message": "Bad request",
            "error_code": "BAD_REQUEST",
        }), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            "success": False,
            "message": "Authentication required",
            "error_code": "UNAUTHORIZED",
        }), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            "success": False,
            "message": "Access denied",
            "error_code": "FORBIDDEN",
        }), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "message": "Resource not found",
            "error_code": "NOT_FOUND",
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            "success": False,
            "message": "Method not allowed",
            "error_code": "METHOD_NOT_ALLOWED",
        }), 405

    @app.errorhandler(409)
    def conflict(error):
        return jsonify({
            "success": False,
            "message": "Resource conflict",
            "error_code": "CONFLICT",
        }), 409

    @app.errorhandler(413)
    def payload_too_large(error):
        return jsonify({
            "success": False,
            "message": "Request payload too large",
            "error_code": "PAYLOAD_TOO_LARGE",
        }), 413

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "message": "Validation error",
            "error_code": "VALIDATION_ERROR",
        }), 422

    @app.errorhandler(429)
    def rate_limited(error):
        return jsonify({
            "success": False,
            "message": "Too many requests — please slow down",
            "error_code": "RATE_LIMIT_EXCEEDED",
        }), 429

    @app.errorhandler(500)
    def internal_error(error):
        logger = get_logger()
        logger.error("Internal server error: %s", error, exc_info=True)
        return jsonify({
            "success": False,
            "message": "An internal error occurred",
            "error_code": "INTERNAL_ERROR",
        }), 500
