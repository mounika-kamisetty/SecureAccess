"""
SecureAssess — Admin Routes.

GET /api/v1/admin/stats
GET /api/v1/admin/audit-logs
"""

from flask import Blueprint, request, g

from app.middleware.auth_middleware import jwt_required
from app.middleware.role_middleware import roles_required
from app.models.user_model import count_users
from app.models.exam_model import count_exams
from app.models.attempt_model import count_attempts
from app.services.audit_service import get_audit_logs
from app.utils.response import success_response
from app.utils.validators import parse_pagination

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/stats", methods=["GET"])
@jwt_required
@roles_required("admin")
def system_stats():
    """Return high-level system statistics."""
    stats = {
        "users": {
            "total": count_users(),
            "students": count_users(role="student"),
            "examiners": count_users(role="examiner"),
            "admins": count_users(role="admin"),
        },
        "exams": {
            "total": count_exams(),
            "draft": count_exams(status="draft"),
            "published": count_exams(status="published"),
            "active": count_exams(status="active"),
            "completed": count_exams(status="completed"),
            "archived": count_exams(status="archived"),
        },
        "attempts": {
            "total": count_attempts(),
        },
    }
    return success_response("System statistics", {"stats": stats})


@admin_bp.route("/audit-logs", methods=["GET"])
@jwt_required
@roles_required("admin")
def audit_logs():
    """Query audit logs (admin only)."""
    skip, limit = parse_pagination(request.args)
    user_id_filter = request.args.get("user_id")
    action_filter = request.args.get("action")

    logs, total = get_audit_logs(
        skip=skip,
        limit=limit,
        user_id=user_id_filter,
        action=action_filter,
    )

    return success_response("Audit logs retrieved", {
        "logs": logs,
        "total": total,
        "page": skip // limit + 1,
        "per_page": limit,
    })
