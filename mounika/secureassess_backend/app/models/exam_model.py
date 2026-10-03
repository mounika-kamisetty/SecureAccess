"""
SecureAssess — Exam Model.

MongoDB CRUD helpers for the ``exams`` collection.
"""

from datetime import datetime, timezone

from bson import ObjectId

from app.extensions.mongo import mongo
from app.models.question_model import serialize_question, serialize_question_safe


# Valid status transitions
VALID_STATUSES = {"draft", "published", "active", "completed", "archived"}


def serialize_exam(doc: dict, safe: bool = False) -> dict:
    """
    Serialise an exam document.

    Args:
        doc: Raw MongoDB document.
        safe: If True, strip correct_answer from every question
              (used for student-facing responses).
    """
    if not doc:
        return {}

    serializer = serialize_question_safe if safe else serialize_question
    questions = [serializer(q) for q in doc.get("questions", [])]

    return {
        "id": str(doc["_id"]),
        "title": doc["title"],
        "description": doc.get("description", ""),
        "duration": doc["duration"],
        "total_marks": doc.get("total_marks", 0),
        "status": doc["status"],
        "start_time": doc["start_time"].isoformat() if doc.get("start_time") else None,
        "end_time": doc["end_time"].isoformat() if doc.get("end_time") else None,
        "created_by": str(doc["created_by"]),
        "questions": questions,
        "question_count": len(questions),
        "created_at": doc["created_at"].isoformat(),
        "updated_at": doc.get("updated_at", doc["created_at"]).isoformat(),
    }


def create_exam(data: dict, created_by: str) -> dict:
    """Insert a new exam in draft status."""
    now = datetime.now(timezone.utc)

    # Calculate total marks from questions
    questions = data.get("questions", [])
    total_marks = sum(q.get("marks", 0) for q in questions)

    # Assign stable question IDs
    for idx, q in enumerate(questions):
        if "question_id" not in q:
            q["question_id"] = f"q_{ObjectId()}"

    doc = {
        "title": data["title"],
        "description": data.get("description", ""),
        "duration": data["duration"],
        "questions": questions,
        "total_marks": total_marks,
        "status": "draft",
        "start_time": data.get("start_time"),
        "end_time": data.get("end_time"),
        "created_by": created_by,
        "created_at": now,
        "updated_at": now,
    }
    result = mongo.exams.insert_one(doc)
    doc["_id"] = result.inserted_id
    return serialize_exam(doc)


def find_exam_by_id(exam_id: str) -> dict | None:
    """Find an exam by ObjectId string."""
    try:
        return mongo.exams.find_one({"_id": ObjectId(exam_id)})
    except Exception:
        return None


def update_exam(exam_id: str, updates: dict) -> bool:
    """Apply partial updates to an exam."""
    updates["updated_at"] = datetime.now(timezone.utc)

    # Recalculate total marks if questions changed
    if "questions" in updates:
        for idx, q in enumerate(updates["questions"]):
            if "question_id" not in q:
                q["question_id"] = f"q_{ObjectId()}"
        updates["total_marks"] = sum(
            q.get("marks", 0) for q in updates["questions"]
        )

    result = mongo.exams.update_one(
        {"_id": ObjectId(exam_id)}, {"$set": updates}
    )
    return result.modified_count > 0


def delete_exam(exam_id: str) -> bool:
    """Soft-delete by archiving the exam."""
    return update_exam(exam_id, {"status": "archived"})


def publish_exam(exam_id: str) -> bool:
    """Move an exam from draft to published."""
    return mongo.exams.update_one(
        {"_id": ObjectId(exam_id), "status": "draft"},
        {"$set": {"status": "published", "updated_at": datetime.now(timezone.utc)}},
    ).modified_count > 0


def list_exams(
    skip: int = 0,
    limit: int = 20,
    status: str | None = None,
    created_by: str | None = None,
) -> list[dict]:
    """List exams with optional filters."""
    query: dict = {}
    if status:
        query["status"] = status
    if created_by:
        query["created_by"] = created_by
    cursor = mongo.exams.find(query).skip(skip).limit(limit).sort("created_at", -1)
    return list(cursor)


def count_exams(status: str | None = None, created_by: str | None = None) -> int:
    """Count exams with optional filters."""
    query: dict = {}
    if status:
        query["status"] = status
    if created_by:
        query["created_by"] = created_by
    return mongo.exams.count_documents(query)
