"""
SecureAssess — Security Utilities.

Password hashing, strength validation, and input sanitisation.
"""

import re

import bcrypt


# ==================================================================
# Password hashing (bcrypt)
# ==================================================================

def hash_password(plain: str) -> str:
    """Hash a plain-text password with bcrypt."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Compare a plain-text password against a bcrypt hash."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# ==================================================================
# Password strength
# ==================================================================

PASSWORD_MIN_LENGTH = 8
PASSWORD_PATTERN = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#^()\-_=+])[A-Za-z\d@$!%*?&#^()\-_=+]{8,}$"
)


def validate_password_strength(password: str) -> list[str]:
    """
    Return a list of weakness messages. Empty list means the password is valid.
    """
    errors: list[str] = []
    if len(password) < PASSWORD_MIN_LENGTH:
        errors.append(f"Password must be at least {PASSWORD_MIN_LENGTH} characters")
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain a lowercase letter")
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain an uppercase letter")
    if not re.search(r"\d", password):
        errors.append("Password must contain a digit")
    if not re.search(r"[@$!%*?&#^()\-_=+]", password):
        errors.append("Password must contain a special character (@$!%*?&#^()-_=+)")
    return errors


# ==================================================================
# Input sanitisation — NoSQL injection prevention
# ==================================================================

def sanitize_input(value):
    """
    Recursively strip MongoDB operator keys ($-prefixed) from dicts.

    Prevents NoSQL injection like {"$gt": ""} or {"$ne": null}.
    """
    if isinstance(value, dict):
        return {
            k: sanitize_input(v)
            for k, v in value.items()
            if not k.startswith("$")
        }
    if isinstance(value, list):
        return [sanitize_input(item) for item in value]
    if isinstance(value, str):
        # Strip any embedded null bytes
        return value.replace("\x00", "")
    return value


def normalize_email(email: str) -> str:
    """Lowercase and strip whitespace from an email address."""
    return email.strip().lower()
