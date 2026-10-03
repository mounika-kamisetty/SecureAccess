"""
SecureAssess — User Management Routes (Admin only).

GET    /api/v1/users
GET    /api/v1/users/<id>
PATCH  /api/v1/users/<id>
DELETE /api/v1/users/<id>      (suspend)
"""

from flask import Blueprint, request, g

from app.middleware.auth_middleware import jwt_required
from app.middleware.role_middleware import roles_required
from app.models.user_model import (
    find_user_by_id,
    serialize_user,
    list_users,
    count_users,
    update_user,
    suspend_user,
    unsuspend_user,
)
from app.models.audit_model import create_audit_log
from app.utils.response import (
    success_response,
    error_response,
    not_found_response,
)
from app.utils.validators import is_valid_object_id, parse_pagination
from app.utils.security import sanitize_input

user_bp = Blueprint("users", __name__, url_prefix="/users")


@user_bp.route("", methods=["GET"])
@jwt_required
@roles_required("admin")
def list_all_users():
    """List all users (admin only)."""
    skip, limit = parse_pagination(request.args)
    role_filter = request.args.get("role")
    users = list_users(skip=skip, limit=limit, role=role_filter)
    total = count_users(role=role_filter)
    return success_response("Users retrieved", {
        "users": users,
        "total": total,
        "page": skip // limit + 1,
        "per_page": limit,
    })


@user_bp.route("/<user_id>", methods=["GET"])
@jwt_required
@roles_required("admin")
def get_user(user_id: str):
    """Get a single user by ID (admin only)."""
    if not is_valid_object_id(user_id):
        return error_response("Invalid user ID", "VALIDATION_ERROR", 422)

    user = find_user_by_id(user_id)
    if not user:
        return not_found_response("User not found")
    return success_response("User retrieved", {"user": serialize_user(user)})


@user_bp.route("/<user_id>", methods=["PATCH"])
@jwt_required
@roles_required("admin")
def update_user_route(user_id: str):
    """Update a user's role or name (admin only)."""
    if not is_valid_object_id(user_id):
        return error_response("Invalid user ID", "VALIDATION_ERROR", 422)

    data = sanitize_input(request.get_json(silent=True) or {})

    # Only allow safe fields
    allowed = {}
    if "name" in data:
        allowed["name"] = str(data["name"]).strip()
    if "role" in data and data["role"] in ("student", "examiner", "admin"):
        allowed["role"] = data["role"]

    if not allowed:
        return error_response("No valid fields to update", "VALIDATION_ERROR", 422)

    if not update_user(user_id, allowed):
        return not_found_response("User not found")

    ip = request.remote_addr or ""
    ua = request.headers.get("User-Agent", "")
    create_audit_log(
        "USER_UPDATED", user_id=g.current_user["user_id"],
        role="admin", resource="user", resource_id=user_id,
        ip_address=ip, user_agent=ua,
    )

    user = find_user_by_id(user_id)
    return success_response("User updated", {"user": serialize_user(user)})


@user_bp.route("/<user_id>", methods=["DELETE"])
@jwt_required
@roles_required("admin")
def suspend_user_route(user_id: str):
    """Suspend a user account (admin only)."""
    if not is_valid_object_id(user_id):
        return error_response("Invalid user ID", "VALIDATION_ERROR", 422)

    # Prevent self-suspension
    if user_id == g.current_user["user_id"]:
        return error_response("Cannot suspend your own account", "FORBIDDEN", 403)

    user = find_user_by_id(user_id)
    if not user:
        return not_found_response("User not found")

    if user.get("is_suspended"):
        # Toggle: unsuspend
        unsuspend_user(user_id)
        action = "USER_UNSUSPENDED"
        msg = "User unsuspended"
    else:
        suspend_user(user_id)
        action = "USER_SUSPENDED"
        msg = "User suspended"

    ip = request.remote_addr or ""
    ua = request.headers.get("User-Agent", "")
    create_audit_log(
        action, user_id=g.current_user["user_id"],
        role="admin", resource="user", resource_id=user_id,
        ip_address=ip, user_agent=ua,
    )

    return success_response(msg)
