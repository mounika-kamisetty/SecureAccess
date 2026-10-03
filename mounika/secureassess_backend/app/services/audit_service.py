"""
SecureAssess — Audit Service.

Thin service layer over the audit model for route-level convenience.
"""

from app.models.audit_model import list_audit_logs, count_audit_logs


def get_audit_logs(
    skip: int = 0,
    limit: int = 50,
    user_id: str | None = None,
    action: str | None = None,
) -> tuple[list[dict], int]:
    """Return paginated audit logs with optional filters."""
    logs = list_audit_logs(skip=skip, limit=limit, user_id=user_id, action=action)
    total = count_audit_logs(user_id=user_id, action=action)
    return logs, total
