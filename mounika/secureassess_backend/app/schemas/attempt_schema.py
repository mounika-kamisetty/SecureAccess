"""
SecureAssess — Attempt Schemas (Pydantic v2).

Request validation for attempt and event endpoints.
"""

from typing import Optional

from pydantic import BaseModel, field_validator

from app.models.event_model import VALID_EVENT_TYPES


class StartAttemptSchema(BaseModel):
    """POST /api/v1/attempts/start"""

    exam_id: str

    @field_validator("exam_id")
    @classmethod
    def exam_id_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("exam_id is required")
        return v


class SaveAnswerSchema(BaseModel):
    """PUT /api/v1/attempts/<id>/answer"""

    question_id: str
    answer: str

    @field_validator("question_id")
    @classmethod
    def qid_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("question_id is required")
        return v

    @field_validator("answer")
    @classmethod
    def answer_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("answer is required")
        return v


class EventSchema(BaseModel):
    """POST /api/v1/events"""

    attempt_id: str
    event_type: str
    metadata: Optional[dict] = None

    @field_validator("attempt_id")
    @classmethod
    def attempt_id_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("attempt_id is required")
        return v

    @field_validator("event_type")
    @classmethod
    def valid_event_type(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in VALID_EVENT_TYPES:
            raise ValueError(
                f"event_type must be one of: {', '.join(sorted(VALID_EVENT_TYPES))}"
            )
        return v
