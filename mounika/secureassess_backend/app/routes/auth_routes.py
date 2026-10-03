"""
SecureAssess — Auth Routes.

POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
GET  /api/v1/auth/me
POST /api/v1/auth/change-password
"""

from flask import Blueprint, request

from pydantic import ValidationError

from app.schemas.auth_schema import (
    RegisterSchema,
    LoginSchema,
    ChangePasswordSchema,
    RefreshSchema,
)
from app.services.auth_service import (
    register_user,
    login_user,
    refresh_access_token,
    logout_user,
    change_password,
    get_current_user,
)
from app.middleware.auth_middleware import jwt_required
from app.utils.response import (
    success_response,
    created_response,
    error_response,
    validation_error_response,
    unauthorized_response,
)
from app.utils.security import sanitize_input

from flask import g

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user."""
    data = sanitize_input(request.get_json(silent=True) or {})

    try:
        schema = RegisterSchema(**data)
    except ValidationError as exc:
        errors = [e["msg"] for e in exc.errors()]
        return validation_error_response("Invalid registration data", errors)

    user, err = register_user(
        name=schema.name,
        email=schema.email,
        password=schema.password,
        role=schema.role,
    )
    if err:
        return error_response(err, "CONFLICT", 409)

    return created_response("Registration successful", {"user": user})


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate and return tokens."""
    data = sanitize_input(request.get_json(silent=True) or {})

    try:
        schema = LoginSchema(**data)
    except ValidationError as exc:
        errors = [e["msg"] for e in exc.errors()]
        return validation_error_response("Invalid login data", errors)

    result, err = login_user(schema.email, schema.password)
    if err:
        return error_response(err, "UNAUTHORIZED", 401)

    return success_response("Login successful", result)


@auth_bp.route("/refresh", methods=["POST"])
def refresh():
    """Issue a new access token using a refresh token."""
    data = sanitize_input(request.get_json(silent=True) or {})

    try:
        schema = RefreshSchema(**data)
    except ValidationError as exc:
        errors = [e["msg"] for e in exc.errors()]
        return validation_error_response("Invalid refresh data", errors)

    result, err = refresh_access_token(schema.refresh_token)
    if err:
        return unauthorized_response(err)

    return success_response("Token refreshed", result)


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Revoke the refresh token."""
    data = sanitize_input(request.get_json(silent=True) or {})
    refresh_token = data.get("refresh_token", "")

    if not refresh_token:
        return error_response("refresh_token is required", "VALIDATION_ERROR", 422)

    ok, err = logout_user(refresh_token)
    if not ok:
        return error_response(err or "Logout failed", "ERROR", 400)

    return success_response("Logged out successfully")


@auth_bp.route("/me", methods=["GET"])
@jwt_required
def me():
    """Return the authenticated user's profile."""
    user_id = g.current_user["user_id"]
    user, err = get_current_user(user_id)
    if err:
        return error_response(err, "NOT_FOUND", 404)
    return success_response("User profile", {"user": user})


@auth_bp.route("/change-password", methods=["POST"])
@jwt_required
def change_pwd():
    """Change the authenticated user's password."""
    data = sanitize_input(request.get_json(silent=True) or {})

    try:
        schema = ChangePasswordSchema(**data)
    except ValidationError as exc:
        errors = [e["msg"] for e in exc.errors()]
        return validation_error_response("Invalid data", errors)

    user_id = g.current_user["user_id"]
    ok, err = change_password(user_id, schema.current_password, schema.new_password)
    if not ok:
        return error_response(err or "Failed to change password", "ERROR", 400)

    return success_response("Password changed successfully")
