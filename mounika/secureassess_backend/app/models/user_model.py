"""
SecureAssess — User Model.

MongoDB CRUD helpers for the ``users`` collection.
"""

from datetime import datetime, timezone

from bson import ObjectId

from app.extensions.mongo import mongo
from app.utils.security import hash_password


def serialize_user(doc: dict) -> dict:
    """Convert a MongoDB user document to a safe JSON-serialisable dict."""
    if not doc:
        return {}
    return {
        "id": str(doc["_id"]),
        "name": doc["name"],
        "email": doc["email"],
        "role": doc["role"],
        "is_suspended": doc.get("is_suspended", False),
        "created_at": doc["created_at"].isoformat(),
        "updated_at": doc.get("updated_at", doc["created_at"]).isoformat(),
    }


def create_user(name: str, email: str, password: str, role: str = "student") -> dict:
    """Insert a new user with a hashed password. Returns the serialised user."""
    now = datetime.now(timezone.utc)
    doc = {
        "name": name,
        "email": email,
        "password_hash": hash_password(password),
        "role": role,
        "is_suspended": False,
        "created_at": now,
        "updated_at": now,
    }
    result = mongo.users.insert_one(doc)
    doc["_id"] = result.inserted_id
    return serialize_user(doc)


def find_user_by_email(email: str) -> dict | None:
    """Find a user by email (case-insensitive, already normalised)."""
    return mongo.users.find_one({"email": email})


def find_user_by_id(user_id: str) -> dict | None:
    """Find a user by ObjectId string."""
    try:
        return mongo.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return None


def update_user(user_id: str, updates: dict) -> bool:
    """Apply partial updates to a user document."""
    updates["updated_at"] = datetime.now(timezone.utc)
    result = mongo.users.update_one(
        {"_id": ObjectId(user_id)}, {"$set": updates}
    )
    return result.modified_count > 0


def suspend_user(user_id: str) -> bool:
    """Suspend a user account."""
    return update_user(user_id, {"is_suspended": True})


def unsuspend_user(user_id: str) -> bool:
    """Re-activate a suspended user account."""
    return update_user(user_id, {"is_suspended": False})


def list_users(skip: int = 0, limit: int = 20, role: str | None = None) -> list[dict]:
    """Return a paginated list of users, optionally filtered by role."""
    query = {}
    if role:
        query["role"] = role
    cursor = mongo.users.find(query).skip(skip).limit(limit).sort("created_at", -1)
    return [serialize_user(u) for u in cursor]


def count_users(role: str | None = None) -> int:
    """Count users, optionally filtered by role."""
    query = {}
    if role:
        query["role"] = role
    return mongo.users.count_documents(query)
