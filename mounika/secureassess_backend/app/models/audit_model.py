"""
SecureAssess — Audit Log Model.

Append-only audit trail. Not editable by normal users.
"""

from datetime import datetime, timezone

from app.extensions.mongo import mongo


# Known audit actions
AUDIT_ACTIONS = {
    "LOGIN_SUCCESS",
    "LOGIN_FAILED",
    "REGISTER",
    "LOGOUT",
    "PASSWORD_CHANGED",
    "EXAM_CREATED",
    "EXAM_UPDATED",
    "EXAM_PUBLISHED",
    "EXAM_DELETED",
    "ATTEMPT_STARTED",
    "ANSWER_SAVED",
    "ATTEMPT_SUBMITTED",
    "RISK_EVENT",
    "USER_SUSPENDED",
    "USER_UNSUSPENDED",
    "USER_UPDATED",
    "ADMIN_ACTION",
}


def serialize_audit(doc: dict) -> dict:
    if not doc:
        return {}
    return {
        "id": str(doc["_id"]),
        "user_id": doc.get("user_id", ""),
        "role": doc.get("role", ""),
        "action": doc["action"],
        "resource": doc.get("resource", ""),
        "resource_id": doc.get("resource_id", ""),
        "timestamp": doc["timestamp"].isoformat(),
        "ip_address": doc.get("ip_address", ""),
        "user_agent": doc.get("user_agent", ""),
        "success": doc.get("success", True),
        "details": doc.get("details", ""),
    }


def create_audit_log(
    action: str,
    user_id: str = "",
    role: str = "",
    resource: str = "",
    resource_id: str = "",
    ip_address: str = "",
    user_agent: str = "",
    success: bool = True,
    details: str = "",
):
    """Append an audit log entry. Returns None (fire-and-forget)."""
    doc = {
        "user_id": user_id,
        "role": role,
        "action": action,
        "resource": resource,
        "resource_id": resource_id,
        "timestamp": datetime.now(timezone.utc),
        "ip_address": ip_address,
        "user_agent": user_agent,
        "success": success,
        "details": details,
    }
    mongo.audit_logs.insert_one(doc)


def list_audit_logs(
    skip: int = 0,
    limit: int = 50,
    user_id: str | None = None,
    action: str | None = None,
) -> list[dict]:
    """Query audit logs with optional filters."""
    query: dict = {}
    if user_id:
        query["user_id"] = user_id
    if action:
        query["action"] = action
    cursor = (
        mongo.audit_logs.find(query)
        .skip(skip)
        .limit(limit)
        .sort("timestamp", -1)
    )
    return [serialize_audit(a) for a in cursor]


def count_audit_logs(user_id: str | None = None, action: str | None = None) -> int:
    query: dict = {}
    if user_id:
        query["user_id"] = user_id
    if action:
        query["action"] = action
    return mongo.audit_logs.count_documents(query)
