"""
SecureAssess — Exam Service.

Business logic for exam lifecycle: create, update, publish, list, delete.
Enforces ownership and role checks.
"""

from flask import request as flask_request

from app.models.exam_model import (
    create_exam,
    find_exam_by_id,
    update_exam,
    delete_exam,
    publish_exam,
    list_exams,
    count_exams,
    serialize_exam,
)
from app.models.audit_model import create_audit_log


def _audit(action, user_id, role, exam_id=""):
    ip = flask_request.remote_addr or ""
    ua = flask_request.headers.get("User-Agent", "")
    create_audit_log(
        action, user_id=user_id, role=role,
        resource="exam", resource_id=exam_id,
        ip_address=ip, user_agent=ua,
    )


def create_new_exam(data: dict, user_id: str, role: str) -> tuple[dict, str | None]:
    """Create a new exam in draft status."""
    exam = create_exam(data, created_by=user_id)
    _audit("EXAM_CREATED", user_id, role, exam["id"])
    return exam, None


def get_exam(exam_id: str, role: str, user_id: str) -> tuple[dict, str | None]:
    """
    Retrieve a single exam.

    Students see the safe version (no correct_answer).
    Examiners see full details only for their own exams.
    Admins see everything.
    """
    doc = find_exam_by_id(exam_id)
    if not doc:
        return {}, "Exam not found"

    if role == "student":
        # Students can only see published / active exams
        if doc["status"] not in ("published", "active"):
            return {}, "Exam not found"
        return serialize_exam(doc, safe=True), None

    if role == "examiner":
        if str(doc["created_by"]) != user_id:
            return {}, "You can only view your own exams"
        return serialize_exam(doc, safe=False), None

    # Admin
    return serialize_exam(doc, safe=False), None


def update_existing_exam(
    exam_id: str, data: dict, user_id: str, role: str
) -> tuple[dict, str | None]:
    """Update an exam (only in draft status, only by owner or admin)."""
    doc = find_exam_by_id(exam_id)
    if not doc:
        return {}, "Exam not found"

    # Ownership check (admin bypasses)
    if role != "admin" and str(doc["created_by"]) != user_id:
        return {}, "You can only update your own exams"

    if doc["status"] != "draft":
        return {}, "Only draft exams can be updated"

    # Build update dict from non-None fields
    updates = {}
    if "title" in data and data["title"] is not None:
        updates["title"] = data["title"]
    if "description" in data and data["description"] is not None:
        updates["description"] = data["description"]
    if "duration" in data and data["duration"] is not None:
        updates["duration"] = data["duration"]
    if "questions" in data and data["questions"] is not None:
        updates["questions"] = data["questions"]
    if "start_time" in data:
        updates["start_time"] = data["start_time"]
    if "end_time" in data:
        updates["end_time"] = data["end_time"]

    if not updates:
        return {}, "No fields to update"

    update_exam(exam_id, updates)
    updated_doc = find_exam_by_id(exam_id)
    _audit("EXAM_UPDATED", user_id, role, exam_id)
    return serialize_exam(updated_doc, safe=False), None


def publish_existing_exam(
    exam_id: str, user_id: str, role: str
) -> tuple[dict, str | None]:
    """Publish a draft exam (makes it visible to students)."""
    doc = find_exam_by_id(exam_id)
    if not doc:
        return {}, "Exam not found"

    if role != "admin" and str(doc["created_by"]) != user_id:
        return {}, "You can only publish your own exams"

    if doc["status"] != "draft":
        return {}, "Only draft exams can be published"

    if not doc.get("questions"):
        return {}, "Cannot publish an exam with no questions"

    if not publish_exam(exam_id):
        return {}, "Failed to publish exam"

    updated_doc = find_exam_by_id(exam_id)
    _audit("EXAM_PUBLISHED", user_id, role, exam_id)
    return serialize_exam(updated_doc, safe=False), None


def delete_existing_exam(
    exam_id: str, user_id: str, role: str
) -> tuple[bool, str | None]:
    """Soft-delete (archive) an exam."""
    doc = find_exam_by_id(exam_id)
    if not doc:
        return False, "Exam not found"

    if role != "admin" and str(doc["created_by"]) != user_id:
        return False, "You can only delete your own exams"

    delete_exam(exam_id)
    _audit("EXAM_DELETED", user_id, role, exam_id)
    return True, None


def list_available_exams(
    role: str,
    user_id: str,
    skip: int = 0,
    limit: int = 20,
    status: str | None = None,
) -> tuple[list[dict], int]:
    """
    List exams based on the caller's role.

    Students: only published/active exams (safe serialisation).
    Examiners: only their own exams.
    Admin: all exams.
    """
    if role == "student":
        # Force status filter for students
        if status and status not in ("published", "active"):
            return [], 0
        if not status:
            # Show both published and active
            docs_pub = list_exams(skip=skip, limit=limit, status="published")
            docs_act = list_exams(skip=skip, limit=limit, status="active")
            docs = docs_pub + docs_act
            total = count_exams(status="published") + count_exams(status="active")
            return [serialize_exam(d, safe=True) for d in docs], total

        docs = list_exams(skip=skip, limit=limit, status=status)
        total = count_exams(status=status)
        return [serialize_exam(d, safe=True) for d in docs], total

    if role == "examiner":
        docs = list_exams(skip=skip, limit=limit, status=status, created_by=user_id)
        total = count_exams(status=status, created_by=user_id)
        return [serialize_exam(d, safe=False) for d in docs], total

    # Admin sees all
    docs = list_exams(skip=skip, limit=limit, status=status)
    total = count_exams(status=status)
    return [serialize_exam(d, safe=False) for d in docs], total
