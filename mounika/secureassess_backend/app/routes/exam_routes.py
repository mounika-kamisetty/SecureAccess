"""
SecureAssess — Exam Routes.

POST   /api/v1/exams
GET    /api/v1/exams
GET    /api/v1/exams/<id>
PUT    /api/v1/exams/<id>
DELETE /api/v1/exams/<id>
PATCH  /api/v1/exams/<id>/publish
"""

from flask import Blueprint, request, g

from pydantic import ValidationError

from app.schemas.exam_schema import CreateExamSchema, UpdateExamSchema
from app.services.exam_service import (
    create_new_exam,
    get_exam,
    update_existing_exam,
    publish_existing_exam,
    delete_existing_exam,
    list_available_exams,
)
from app.middleware.auth_middleware import jwt_required
from app.middleware.role_middleware import roles_required
from app.utils.response import (
    success_response,
    created_response,
    error_response,
    not_found_response,
    validation_error_response,
    forbidden_response,
)
from app.utils.validators import is_valid_object_id, parse_pagination
from app.utils.security import sanitize_input

exam_bp = Blueprint("exams", __name__, url_prefix="/exams")


@exam_bp.route("", methods=["POST"])
@jwt_required
@roles_required("examiner", "admin")
def create_exam():
    """Create a new exam (examiner/admin only)."""
    data = sanitize_input(request.get_json(silent=True) or {})

    try:
        schema = CreateExamSchema(**data)
    except ValidationError as exc:
        errors = [e["msg"] for e in exc.errors()]
        return validation_error_response("Invalid exam data", errors)

    user = g.current_user
    exam, err = create_new_exam(
        data=schema.model_dump(),
        user_id=user["user_id"],
        role=user["role"],
    )
    if err:
        return error_response(err)

    return created_response("Exam created", {"exam": exam})


@exam_bp.route("", methods=["GET"])
@jwt_required
def list_exams_route():
    """List exams (role-aware filtering)."""
    user = g.current_user
    skip, limit = parse_pagination(request.args)
    status = request.args.get("status")

    exams, total = list_available_exams(
        role=user["role"],
        user_id=user["user_id"],
        skip=skip,
        limit=limit,
        status=status,
    )

    return success_response("Exams retrieved", {
        "exams": exams,
        "total": total,
        "page": skip // limit + 1,
        "per_page": limit,
    })


@exam_bp.route("/<exam_id>", methods=["GET"])
@jwt_required
def get_exam_route(exam_id: str):
    """Get a single exam."""
    if not is_valid_object_id(exam_id):
        return error_response("Invalid exam ID", "VALIDATION_ERROR", 422)

    user = g.current_user
    exam, err = get_exam(exam_id, user["role"], user["user_id"])
    if err:
        if "not found" in err.lower():
            return not_found_response(err)
        return forbidden_response(err)

    return success_response("Exam retrieved", {"exam": exam})


@exam_bp.route("/<exam_id>", methods=["PUT"])
@jwt_required
@roles_required("examiner", "admin")
def update_exam_route(exam_id: str):
    """Update an exam (draft only, owner/admin only)."""
    if not is_valid_object_id(exam_id):
        return error_response("Invalid exam ID", "VALIDATION_ERROR", 422)

    data = sanitize_input(request.get_json(silent=True) or {})

    try:
        schema = UpdateExamSchema(**data)
    except ValidationError as exc:
        errors = [e["msg"] for e in exc.errors()]
        return validation_error_response("Invalid exam data", errors)

    user = g.current_user
    exam, err = update_existing_exam(
        exam_id=exam_id,
        data=schema.model_dump(exclude_none=True),
        user_id=user["user_id"],
        role=user["role"],
    )
    if err:
        if "not found" in err.lower():
            return not_found_response(err)
        return error_response(err, "FORBIDDEN", 403)

    return success_response("Exam updated", {"exam": exam})


@exam_bp.route("/<exam_id>", methods=["DELETE"])
@jwt_required
@roles_required("examiner", "admin")
def delete_exam_route(exam_id: str):
    """Soft-delete (archive) an exam."""
    if not is_valid_object_id(exam_id):
        return error_response("Invalid exam ID", "VALIDATION_ERROR", 422)

    user = g.current_user
    ok, err = delete_existing_exam(exam_id, user["user_id"], user["role"])
    if not ok:
        if "not found" in (err or "").lower():
            return not_found_response(err)
        return forbidden_response(err)

    return success_response("Exam archived")


@exam_bp.route("/<exam_id>/publish", methods=["PATCH"])
@jwt_required
@roles_required("examiner", "admin")
def publish_exam_route(exam_id: str):
    """Publish a draft exam."""
    if not is_valid_object_id(exam_id):
        return error_response("Invalid exam ID", "VALIDATION_ERROR", 422)

    user = g.current_user
    exam, err = publish_existing_exam(exam_id, user["user_id"], user["role"])
    if err:
        if "not found" in err.lower():
            return not_found_response(err)
        return error_response(err, "ERROR", 400)

    return success_response("Exam published", {"exam": exam})
