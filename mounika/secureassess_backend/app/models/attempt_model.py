"""
SecureAssess — Attempt Model.

MongoDB CRUD for the ``attempts`` collection.
An attempt tracks a student's session for one exam.
"""

from datetime import datetime, timezone

from bson import ObjectId

from app.extensions.mongo import mongo


ATTEMPT_STATUSES = {"in_progress", "submitted", "expired", "auto_submitted"}


def serialize_attempt(doc: dict, include_answers: bool = False) -> dict:
    """Serialise an attempt. Answers are optional (for listing)."""
    if not doc:
        return {}

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    expiry = doc["expiry_time"]
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)
    remaining = (expiry - now).total_seconds()

    result = {
        "id": str(doc["_id"]),
        "exam_id": str(doc["exam_id"]),
        "user_id": str(doc["user_id"]),
        "status": doc["status"],
        "start_time": doc["start_time"].isoformat(),
        "expiry_time": doc["expiry_time"].isoformat(),
        "remaining_seconds": max(0, int(remaining)),
        "submitted_at": doc["submitted_at"].isoformat() if doc.get("submitted_at") else None,
        "score": doc.get("score"),
        "max_score": doc.get("max_score"),
        "percentage": doc.get("percentage"),
        "risk_score": doc.get("risk_score", 0),
        "risk_level": doc.get("risk_level", "low"),
        "question_order": doc.get("question_order", []),
        "created_at": doc["created_at"].isoformat(),
    }

    if include_answers:
        result["answers"] = doc.get("answers", {})

    return result


def create_attempt(
    user_id: str,
    exam_id: str,
    question_order: list[str],
    duration_minutes: int,
) -> dict:
    """Create a new exam attempt with server-side timing."""
    now = datetime.now(timezone.utc)
    from datetime import timedelta

    expiry_time = now + timedelta(minutes=duration_minutes)

    doc = {
        "user_id": user_id,
        "exam_id": exam_id,
        "status": "in_progress",
        "start_time": now,
        "expiry_time": expiry_time,
        "submitted_at": None,
        "answers": {},
        "score": None,
        "max_score": None,
        "percentage": None,
        "risk_score": 0,
        "risk_level": "low",
        "question_order": question_order,
        "created_at": now,
    }
    result = mongo.attempts.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


def find_attempt_by_id(attempt_id: str) -> dict | None:
    """Find an attempt by ObjectId string."""
    try:
        return mongo.attempts.find_one({"_id": ObjectId(attempt_id)})
    except Exception:
        return None


def find_active_attempt(user_id: str, exam_id: str) -> dict | None:
    """Check if the student already has an active attempt for this exam."""
    return mongo.attempts.find_one({
        "user_id": user_id,
        "exam_id": exam_id,
        "status": "in_progress",
    })


def save_answer(attempt_id: str, question_id: str, answer: str) -> bool:
    """Save or overwrite a single answer in an active attempt."""
    now = datetime.now(timezone.utc)
    result = mongo.attempts.update_one(
        {"_id": ObjectId(attempt_id), "status": "in_progress"},
        {
            "$set": {
                f"answers.{question_id}": {
                    "answer": answer,
                    "saved_at": now,
                }
            }
        },
    )
    return result.modified_count > 0


def submit_attempt(attempt_id: str, score_data: dict) -> bool:
    """
    Lock an attempt and write the final score.

    score_data must contain: score, max_score, percentage, risk_score, risk_level.
    """
    now = datetime.now(timezone.utc)
    result = mongo.attempts.update_one(
        {"_id": ObjectId(attempt_id), "status": "in_progress"},
        {
            "$set": {
                "status": "submitted",
                "submitted_at": now,
                "score": score_data["score"],
                "max_score": score_data["max_score"],
                "percentage": score_data["percentage"],
                "risk_score": score_data["risk_score"],
                "risk_level": score_data["risk_level"],
            }
        },
    )
    return result.modified_count > 0


def list_attempts_by_user(user_id: str, skip: int = 0, limit: int = 20) -> list[dict]:
    """List attempts for a specific user."""
    cursor = (
        mongo.attempts.find({"user_id": user_id})
        .skip(skip)
        .limit(limit)
        .sort("created_at", -1)
    )
    return list(cursor)


def list_attempts_by_exam(exam_id: str, skip: int = 0, limit: int = 20) -> list[dict]:
    """List all attempts for a specific exam (examiner/admin view)."""
    cursor = (
        mongo.attempts.find({"exam_id": exam_id})
        .skip(skip)
        .limit(limit)
        .sort("created_at", -1)
    )
    return list(cursor)


def count_attempts(user_id: str | None = None, exam_id: str | None = None) -> int:
    """Count attempts with optional filters."""
    query: dict = {}
    if user_id:
        query["user_id"] = user_id
    if exam_id:
        query["exam_id"] = exam_id
    return mongo.attempts.count_documents(query)
