"""
SecureAssess — Event Routes (Anti-Malpractice).

POST /api/v1/events
GET  /api/v1/events/<attempt_id>   (examiner/admin)
"""

from flask import Blueprint, request, g

from pydantic import ValidationError

from app.schemas.attempt_schema import EventSchema
from app.models.event_model import create_event, find_events_by_attempt
from app.models.attempt_model import find_attempt_by_id
from app.models.exam_model import find_exam_by_id
from app.models.audit_model import create_audit_log
from app.services.risk_service import get_risk_breakdown
from app.middleware.auth_middleware import jwt_required
from app.middleware.role_middleware import roles_required
from app.utils.response import (
    success_response,
    created_response,
    error_response,
    forbidden_response,
    validation_error_response,
    not_found_response,
)
from app.utils.validators import is_valid_object_id
from app.utils.security import sanitize_input

event_bp = Blueprint("events", __name__, url_prefix="/events")


@event_bp.route("", methods=["POST"])
@jwt_required
@roles_required("student")
def record_event():
    """
    Record an anti-malpractice event.

    The student's frontend reports events; the server records them
    and the risk engine scores them. Students cannot set risk_score.
    """
    data = sanitize_input(request.get_json(silent=True) or {})

    try:
        schema = EventSchema(**data)
    except ValidationError as exc:
        errors = [e["msg"] for e in exc.errors()]
        return validation_error_response("Invalid event data", errors)

    if not is_valid_object_id(schema.attempt_id):
        return error_response("Invalid attempt ID", "VALIDATION_ERROR", 422)

    # Verify attempt ownership
    attempt = find_attempt_by_id(schema.attempt_id)
    if not attempt:
        return not_found_response("Attempt not found")

    user = g.current_user
    if str(attempt["user_id"]) != user["user_id"]:
        return forbidden_response("Access denied")

    if attempt["status"] != "in_progress":
        return error_response("Attempt is no longer active")

    ip = request.remote_addr or ""
    ua = request.headers.get("User-Agent", "")

    event = create_event(
        attempt_id=schema.attempt_id,
        user_id=user["user_id"],
        event_type=schema.event_type,
        ip_address=ip,
        user_agent=ua,
        metadata=schema.metadata,
    )

    # Audit
    create_audit_log(
        "RISK_EVENT", user_id=user["user_id"], role=user["role"],
        resource="event", resource_id=event["id"],
        ip_address=ip, user_agent=ua,
        details=f"Event: {schema.event_type}",
    )

    return created_response("Event recorded", {"event": event})


@event_bp.route("/<attempt_id>", methods=["GET"])
@jwt_required
@roles_required("examiner", "admin")
def get_events(attempt_id: str):
    """
    Get all events and risk breakdown for an attempt (examiner/admin).

    Examiners can only view events for attempts on their own exams.
    """
    if not is_valid_object_id(attempt_id):
        return error_response("Invalid attempt ID", "VALIDATION_ERROR", 422)

    attempt = find_attempt_by_id(attempt_id)
    if not attempt:
        return not_found_response("Attempt not found")

    user = g.current_user
    if user["role"] == "examiner":
        exam = find_exam_by_id(str(attempt["exam_id"]))
        if not exam or str(exam["created_by"]) != user["user_id"]:
            return forbidden_response("Access denied")

    events = find_events_by_attempt(attempt_id)
    risk = get_risk_breakdown(attempt_id)

    return success_response("Events retrieved", {
        "events": events,
        "risk": risk,
    })
