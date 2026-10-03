"""
SecureAssess — Auth Schemas (Pydantic v2).

Request validation for authentication endpoints.
"""

from pydantic import BaseModel, EmailStr, field_validator

from app.utils.security import validate_password_strength, normalize_email


VALID_ROLES = {"student", "examiner", "admin"}


class RegisterSchema(BaseModel):
    """POST /api/v1/auth/register"""

    name: str
    email: EmailStr
    password: str
    role: str = "student"

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v or len(v) < 2:
            raise ValueError("Name must be at least 2 characters")
        if len(v) > 100:
            raise ValueError("Name must be at most 100 characters")
        return v

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        return normalize_email(v)

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        errors = validate_password_strength(v)
        if errors:
            raise ValueError("; ".join(errors))
        return v

    @field_validator("role")
    @classmethod
    def valid_role(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in VALID_ROLES:
            raise ValueError(f"Role must be one of: {', '.join(sorted(VALID_ROLES))}")
        return v


class LoginSchema(BaseModel):
    """POST /api/v1/auth/login"""

    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        return normalize_email(v)


class ChangePasswordSchema(BaseModel):
    """POST /api/v1/auth/change-password"""

    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def strong_new_password(cls, v: str) -> str:
        errors = validate_password_strength(v)
        if errors:
            raise ValueError("; ".join(errors))
        return v


class RefreshSchema(BaseModel):
    """POST /api/v1/auth/refresh"""

    refresh_token: str
