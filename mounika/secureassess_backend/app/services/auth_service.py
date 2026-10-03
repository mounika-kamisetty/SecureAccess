"""
SecureAssess — Auth Service.

Business logic for registration, login, token refresh, logout,
and password change.
"""

from flask import request as flask_request

from flask_jwt_extended import create_access_token, create_refresh_token, decode_token
from flask_jwt_extended.exceptions import JWTExtendedException

from app.extensions.jwt_manager import revoke_token, revoke_all_user_tokens
from app.models.user_model import (
    create_user,
    find_user_by_email,
    find_user_by_id,
    serialize_user,
    update_user,
)
from app.models.audit_model import create_audit_log
from app.utils.security import verify_password, hash_password, normalize_email


def _client_info() -> tuple[str, str]:
    """Extract client IP and User-Agent from the current request."""
    ip = flask_request.remote_addr or ""
    ua = flask_request.headers.get("User-Agent", "")
    return ip, ua


def register_user(name: str, email: str, password: str, role: str) -> tuple[dict, str | None]:
    """
    Register a new user.

    Returns (user_dict, error_message).
    On success error_message is None.
    """
    email = normalize_email(email)
    ip, ua = _client_info()

    # Check for duplicate
    if find_user_by_email(email):
        create_audit_log(
            "REGISTER", user_id="", role=role,
            resource="user", ip_address=ip, user_agent=ua,
            success=False, details=f"Duplicate email: {email}",
        )
        return {}, "A user with this email already exists"

    user = create_user(name, email, password, role)

    create_audit_log(
        "REGISTER", user_id=user["id"], role=role,
        resource="user", resource_id=user["id"],
        ip_address=ip, user_agent=ua,
    )
    return user, None


def login_user(email: str, password: str) -> tuple[dict, str | None]:
    """
    Authenticate a user and issue tokens.

    Returns (response_data, error_message).
    """
    email = normalize_email(email)
    ip, ua = _client_info()

    user = find_user_by_email(email)
    if not user:
        create_audit_log(
            "LOGIN_FAILED", ip_address=ip, user_agent=ua,
            success=False, details=f"Unknown email: {email}",
        )
        return {}, "Invalid email or password"

    if user.get("is_suspended"):
        create_audit_log(
            "LOGIN_FAILED", user_id=str(user["_id"]), role=user["role"],
            ip_address=ip, user_agent=ua,
            success=False, details="Account suspended",
        )
        return {}, "Your account has been suspended"

    if not verify_password(password, user["password_hash"]):
        create_audit_log(
            "LOGIN_FAILED", user_id=str(user["_id"]), role=user["role"],
            ip_address=ip, user_agent=ua,
            success=False, details="Wrong password",
        )
        return {}, "Invalid email or password"

    # Issue tokens
    user_id = str(user["_id"])
    access_token = create_access_token(identity=user_id, additional_claims={"role": user["role"]})
    refresh_token = create_refresh_token(identity=user_id, additional_claims={"role": user["role"]})

    create_audit_log(
        "LOGIN_SUCCESS", user_id=user_id, role=user["role"],
        resource="session", ip_address=ip, user_agent=ua,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": serialize_user(user),
    }, None


def refresh_access_token(refresh_token_str: str) -> tuple[dict, str | None]:
    """
    Issue a new access token from a valid refresh token.

    Returns (response_data, error_message).
    """
    try:
        payload = decode_token(refresh_token_str)
        if payload.get("type") != "refresh":
            return {}, "Not a refresh token"
        
        # Manually check blocklist because decode_token doesn't
        from app.extensions.mongo import mongo
        jti = payload.get("jti")
        if mongo.blocklist.find_one({"jti": jti}):
            return {}, "Token has been revoked"
            
    except Exception as exc:
        return {}, str(exc)

    user_id = payload["sub"]
    role = payload.get("role", "student")

    # Verify user still exists and is not suspended
    user = find_user_by_id(user_id)
    if not user:
        return {}, "User not found"
    if user.get("is_suspended"):
        return {}, "Account suspended"

    access_token = create_access_token(identity=user_id, additional_claims={"role": role})

    return {
        "access_token": access_token,
        "user": serialize_user(user),
    }, None


def logout_user(refresh_token_str: str) -> tuple[bool, str | None]:
    """
    Revoke the provided refresh token.

    Returns (success, error_message).
    """
    try:
        payload = decode_token(refresh_token_str)
        jti = payload.get("jti")
        if jti:
            user_id = payload.get("sub", "")
            revoke_token(jti, user_id, payload.get("type", "refresh"))

        ip, ua = _client_info()
        create_audit_log(
            "LOGOUT", user_id=payload.get("sub", ""),
            role=payload.get("role", ""),
            ip_address=ip, user_agent=ua,
        )
        return True, None
    except Exception as exc:
        return False, str(exc)


def change_password(
    user_id: str, current_password: str, new_password: str
) -> tuple[bool, str | None]:
    """
    Change a user's password after verifying the current one.

    Revokes all existing refresh tokens as a security measure.
    """
    ip, ua = _client_info()
    user = find_user_by_id(user_id)
    if not user:
        return False, "User not found"

    if not verify_password(current_password, user["password_hash"]):
        return False, "Current password is incorrect"

    # Update password
    update_user(user_id, {"password_hash": hash_password(new_password)})

    # Revoke all refresh tokens (force re-login everywhere)
    revoke_all_user_tokens(user_id)

    create_audit_log(
        "PASSWORD_CHANGED", user_id=user_id, role=user["role"],
        resource="user", resource_id=user_id,
        ip_address=ip, user_agent=ua,
    )
    return True, None


def get_current_user(user_id: str) -> tuple[dict, str | None]:
    """Return the authenticated user's profile."""
    user = find_user_by_id(user_id)
    if not user:
        return {}, "User not found"
    return serialize_user(user), None
