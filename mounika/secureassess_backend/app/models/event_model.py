"""
SecureAssess — Event Model.

Stores anti-malpractice events reported by the frontend
and queried by the risk engine.
"""

from datetime import datetime, timezone

from bson import ObjectId

from app.extensions.mongo import mongo


VALID_EVENT_TYPES = {
    "tab_switch",
    "window_blur",
    "fullscreen_exit",
    "copy",
    "paste",
    "right_click",
    "devtools_detected",
    "camera_off",
    "no_face",
    "multiple_face",
    "network_disconnect",
    "ip_change",
    "suspicious_answer_pattern",
}


def serialize_event(doc: dict) -> dict:
    """Convert a MongoDB event document to a JSON-safe dict."""
    if not doc:
        return {}
    return {
        "id": str(doc["_id"]),
        "attempt_id": str(doc["attempt_id"]),
        "user_id": str(doc["user_id"]),
        "event_type": doc["event_type"],
        "timestamp": doc["timestamp"].isoformat(),
        "ip_address": doc.get("ip_address", ""),
        "user_agent": doc.get("user_agent", ""),
        "metadata": doc.get("metadata", {}),
    }


def create_event(
    attempt_id: str,
    user_id: str,
    event_type: str,
    ip_address: str = "",
    user_agent: str = "",
    metadata: dict | None = None,
) -> dict:
    """Record a single malpractice event."""
    now = datetime.now(timezone.utc)
    doc = {
        "attempt_id": attempt_id,
        "user_id": user_id,
        "event_type": event_type,
        "timestamp": now,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "metadata": metadata or {},
    }
    result = mongo.events.insert_one(doc)
    doc["_id"] = result.inserted_id
    return serialize_event(doc)


def find_events_by_attempt(attempt_id: str) -> list[dict]:
    """Return all events for a given attempt, newest first."""
    cursor = (
        mongo.events.find({"attempt_id": attempt_id})
        .sort("timestamp", -1)
    )
    return [serialize_event(e) for e in cursor]


def count_events_by_type(attempt_id: str) -> dict[str, int]:
    """
    Count occurrences of each event type for an attempt.

    Returns e.g. {"tab_switch": 3, "copy": 1}
    """
    pipeline = [
        {"$match": {"attempt_id": attempt_id}},
        {"$group": {"_id": "$event_type", "count": {"$sum": 1}}},
    ]
    results = mongo.events.aggregate(pipeline)
    return {r["_id"]: r["count"] for r in results}
