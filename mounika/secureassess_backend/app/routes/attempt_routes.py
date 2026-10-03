"""
SecureAssess — Attempt Routes.

POST /api/v1/attempts/start
PUT  /api/v1/attempts/<id>/answer
GET  /api/v1/attempts/<id>
POST /api/v1/attempts/<id>/submit
GET  /api/v1/attempts/my
"""

from flask import Blueprint, request, g

from pydantic import ValidationError

from app.schemas.attempt_schema import StartAttemptSchema, SaveAnswerSchema
from app.services.attempt_service import (
    start_exam_attempt,
    save_student_answer,
    submit_exam_attempt,
    get_student_attempt,
    get_my_attempts,
)
from app.middleware.auth_middleware import jwt_required
from app.middleware.role_middleware import roles_required
from app.utils.response import (
    success_response,
    created_response,
    error_response,
    not_found_response,
    forbidden_response,
    validation_error_response,
)
from app.utils.validators import is_valid_object_id, parse_pagination
from app.utils.security import sanitize_input

attempt_bp = Blueprint("attempts", __name__, url_prefix="/attempts")


@attempt_bp.route("/start", methods=["POST"])
@jwt_required
@roles_required("student")
def start_attempt():
    """Start a new exam attempt."""
    data = sanitize_input(request.get_json(silent=True) or {})

    try:
        schema = StartAttemptSchema(**data)
    except ValidationError as exc:
        errors = [e["msg"] for e in exc.errors()]
        return validation_error_response("Invalid data", errors)

    if not is_valid_object_id(schema.exam_id):
        return error_response("Invalid exam ID", "VALIDATION_ERROR", 422)

    user = g.current_user
    attempt, err = start_exam_attempt(
        exam_id=schema.exam_id,
        user_id=user["user_id"],
        role=user["role"],
    )
    if err:
        return error_response(err)

    return created_response("Attempt started", {"attempt": attempt})


@attempt_bp.route("/<attempt_id>/answer", methods=["PUT"])
@jwt_required
@roles_required("student")
def save_answer(attempt_id: str):
    """Save a single answer during an active attempt."""
    if not is_valid_object_id(attempt_id):
        return error_response("Invalid attempt ID", "VALIDATION_ERROR", 422)

    data = sanitize_input(request.get_json(silent=True) or {})

    try:
        schema = SaveAnswerSchema(**data)
    except ValidationError as exc:
        errors = [e["msg"] for e in exc.errors()]
        return validation_error_response("Invalid data", errors)

    user = g.current_user
    ok, err = save_student_answer(
        attempt_id=attempt_id,
        question_id=schema.question_id,
        answer=schema.answer,
        user_id=user["user_id"],
        role=user["role"],
    )
    if not ok:
        if "denied" in (err or "").lower():
            return forbidden_response(err)
        return error_response(err or "Failed to save answer")

    return success_response("Answer saved")


@attempt_bp.route("/<attempt_id>", methods=["GET"])
@jwt_required
def get_attempt(attempt_id: str):
    """Get a single attempt (ownership check for students)."""
    if not is_valid_object_id(attempt_id):
        return error_response("Invalid attempt ID", "VALIDATION_ERROR", 422)

    user = g.current_user
    attempt, err = get_student_attempt(attempt_id, user["user_id"], user["role"])
    if err:
        if "denied" in err.lower():
            return forbidden_response(err)
        return not_found_response(err)

    return success_response("Attempt retrieved", {"attempt": attempt})


@attempt_bp.route("/<attempt_id>/submit", methods=["POST"])
@jwt_required
@roles_required("student")
def submit_attempt(attempt_id: str):
    """Submit an exam attempt for server-side scoring."""
    if not is_valid_object_id(attempt_id):
        return error_response("Invalid attempt ID", "VALIDATION_ERROR", 422)

    user = g.current_user
    result, err = submit_exam_attempt(
        attempt_id=attempt_id,
        user_id=user["user_id"],
        role=user["role"],
    )
    if err:
        if "denied" in err.lower():
            return forbidden_response(err)
        return error_response(err)

    return success_response("Exam submitted", {"result": result})


@attempt_bp.route("/my", methods=["GET"])
@jwt_required
@roles_required("student")
def my_attempts():
    """List the authenticated student's attempts."""
    user = g.current_user
    skip, limit = parse_pagination(request.args)

    attempts, total = get_my_attempts(user["user_id"], skip, limit)

    return success_response("Attempts retrieved", {
        "attempts": attempts,
        "total": total,
        "page": skip // limit + 1,
        "per_page": limit,
    })
