"""
SecureAssess — Attempt Service.

Business logic for starting exams, saving answers, and submitting.
All timing and scoring is controlled server-side.
"""

from datetime import datetime, timezone

from flask import request as flask_request

from app.models.attempt_model import (
    create_attempt,
    find_attempt_by_id,
    find_active_attempt,
    save_answer,
    submit_attempt,
    list_attempts_by_user,
    list_attempts_by_exam,
    count_attempts,
    serialize_attempt,
)
from app.models.exam_model import find_exam_by_id
from app.models.question_model import randomize_questions, get_answer_key
from app.models.audit_model import create_audit_log
from app.services.risk_service import calculate_risk_score


def _audit(action, user_id, role, resource_id=""):
    ip = flask_request.remote_addr or ""
    ua = flask_request.headers.get("User-Agent", "")
    create_audit_log(
        action, user_id=user_id, role=role,
        resource="attempt", resource_id=resource_id,
        ip_address=ip, user_agent=ua,
    )


def start_exam_attempt(
    exam_id: str, user_id: str, role: str
) -> tuple[dict, str | None]:
    """
    Start a new exam attempt for a student.

    Validates:
    - Exam exists and is published/active.
    - No duplicate active attempt.
    - Exam timing (if start_time/end_time are set).
    - Generates randomised question order.
    - Sets server-side start and expiry times.
    """
    exam = find_exam_by_id(exam_id)
    if not exam:
        return {}, "Exam not found"

    if exam["status"] not in ("published", "active"):
        return {}, "This exam is not currently available"

    # Check exam timing window
    now = datetime.now(timezone.utc)
    if exam.get("start_time") and now < exam["start_time"]:
        return {}, "This exam has not started yet"
    if exam.get("end_time") and now > exam["end_time"]:
        return {}, "This exam has ended"

    # Prevent duplicate active attempt
    existing = find_active_attempt(user_id, exam_id)
    if existing:
        return serialize_attempt(existing, include_answers=True), None

    # Randomise question order
    shuffled = randomize_questions(exam.get("questions", []))
    question_order = [q["question_id"] for q in shuffled]

    attempt_doc = create_attempt(
        user_id=user_id,
        exam_id=exam_id,
        question_order=question_order,
        duration_minutes=exam["duration"],
    )

    _audit("ATTEMPT_STARTED", user_id, role, str(attempt_doc["_id"]))

    return serialize_attempt(attempt_doc, include_answers=True), None


def save_student_answer(
    attempt_id: str,
    question_id: str,
    answer: str,
    user_id: str,
    role: str,
) -> tuple[bool, str | None]:
    """
    Save a single answer.

    Validates:
    - Attempt exists and belongs to the student.
    - Attempt is still active.
    - Attempt has not expired.
    - Question belongs to the attempt.
    """
    attempt = find_attempt_by_id(attempt_id)
    if not attempt:
        return False, "Attempt not found"

    # Ownership (IDOR protection)
    if str(attempt["user_id"]) != user_id:
        return False, "Access denied"

    if attempt["status"] != "in_progress":
        return False, "This attempt is no longer active"

    # Server-side time check
    now = datetime.now(timezone.utc)
    if now > attempt["expiry_time"].replace(tzinfo=timezone.utc):
        return False, "Time has expired for this attempt"

    # Verify question belongs to this attempt
    if question_id not in attempt.get("question_order", []):
        return False, "Question does not belong to this attempt"

    if not save_answer(attempt_id, question_id, answer):
        return False, "Failed to save answer"

    _audit("ANSWER_SAVED", user_id, role, attempt_id)
    return True, None


def submit_exam_attempt(
    attempt_id: str, user_id: str, role: str
) -> tuple[dict, str | None]:
    """
    Submit an exam attempt.

    Server-side scoring:
    1. Verify attempt ownership and status.
    2. Load exam and correct answers from database.
    3. Compare student answers against the answer key.
    4. Calculate score, percentage, and risk.
    5. Lock the attempt permanently.
    """
    attempt = find_attempt_by_id(attempt_id)
    if not attempt:
        return {}, "Attempt not found"

    if str(attempt["user_id"]) != user_id:
        return {}, "Access denied"

    if attempt["status"] != "in_progress":
        return {}, "This attempt has already been submitted"

    # Load the exam
    exam = find_exam_by_id(str(attempt["exam_id"]))
    if not exam:
        return {}, "Associated exam not found"

    # Build answer key (server-side only)
    answer_key = get_answer_key(exam.get("questions", []))

    # Score the attempt
    student_answers = attempt.get("answers", {})
    score = 0
    max_score = sum(q.get("marks", 0) for q in exam.get("questions", []))

    for q in exam.get("questions", []):
        qid = q["question_id"]
        correct = q.get("correct_answer", "")
        student_entry = student_answers.get(qid, {})
        student_ans = student_entry.get("answer", "") if isinstance(student_entry, dict) else ""

        if student_ans.strip().lower() == correct.strip().lower():
            score += q.get("marks", 0)

    percentage = round((score / max_score * 100), 2) if max_score > 0 else 0

    # Calculate risk score from events
    risk_score, risk_level = calculate_risk_score(attempt_id)

    score_data = {
        "score": score,
        "max_score": max_score,
        "percentage": percentage,
        "risk_score": risk_score,
        "risk_level": risk_level,
    }

    if not submit_attempt(attempt_id, score_data):
        return {}, "Failed to submit attempt (may have already been submitted)"

    _audit("ATTEMPT_SUBMITTED", user_id, role, attempt_id)

    # Return result (safe — no correct answers)
    return {
        "score": score,
        "max_score": max_score,
        "percentage": percentage,
        "status": "submitted",
        "risk_score": risk_score,
        "risk_level": risk_level,
    }, None


def get_student_attempt(
    attempt_id: str, user_id: str, role: str
) -> tuple[dict, str | None]:
    """Get a single attempt (ownership check for students)."""
    attempt = find_attempt_by_id(attempt_id)
    if not attempt:
        return {}, "Attempt not found"

    if role == "student" and str(attempt["user_id"]) != user_id:
        return {}, "Access denied"

    if role == "examiner":
        # Examiner can only see attempts for their own exams
        exam = find_exam_by_id(str(attempt["exam_id"]))
        if not exam or str(exam["created_by"]) != user_id:
            return {}, "Access denied"

    return serialize_attempt(attempt, include_answers=True), None


def get_my_attempts(
    user_id: str, skip: int = 0, limit: int = 20
) -> tuple[list[dict], int]:
    """List all attempts for the authenticated student."""
    docs = list_attempts_by_user(user_id, skip, limit)
    total = count_attempts(user_id=user_id)
    return [serialize_attempt(d) for d in docs], total


def get_exam_attempts(
    exam_id: str, user_id: str, role: str, skip: int = 0, limit: int = 20
) -> tuple[list[dict], int]:
    """List attempts for an exam (examiner sees their own exams, admin sees all)."""
    if role == "examiner":
        exam = find_exam_by_id(exam_id)
        if not exam or str(exam["created_by"]) != user_id:
            return [], 0

    docs = list_attempts_by_exam(exam_id, skip, limit)
    total = count_attempts(exam_id=exam_id)
    return [serialize_attempt(d, include_answers=True) for d in docs], total
