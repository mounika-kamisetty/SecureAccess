"""
SecureAssess — Common Validators.

ObjectId validation, pagination, and other shared checks.
"""

from bson import ObjectId
from bson.errors import InvalidId


def is_valid_object_id(value: str) -> bool:
    """Check whether a string is a valid 24-hex-char MongoDB ObjectId."""
    try:
        ObjectId(value)
        return True
    except (InvalidId, TypeError):
        return False


def to_object_id(value: str) -> ObjectId:
    """Convert a string to ObjectId or raise ValueError."""
    if not is_valid_object_id(value):
        raise ValueError(f"Invalid ID format: {value}")
    return ObjectId(value)


def parse_pagination(args: dict) -> tuple[int, int]:
    """
    Extract page & per_page from query string args.

    Returns (skip, limit) suitable for MongoDB .skip().limit().
    """
    try:
        page = max(int(args.get("page", 1)), 1)
        per_page = min(max(int(args.get("per_page", 20)), 1), 100)
    except (ValueError, TypeError):
        page, per_page = 1, 20

    skip = (page - 1) * per_page
    return skip, per_page
