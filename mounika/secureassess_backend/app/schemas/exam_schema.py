"""
SecureAssess — Exam Schemas (Pydantic v2).

Request validation for exam CRUD endpoints.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


VALID_QUESTION_TYPES = {"mcq", "true_false", "multiple_choice"}


class QuestionSchema(BaseModel):
    """Schema for a single question embedded in an exam."""

    text: str
    type: str = "mcq"
    options: list[str]
    marks: int = 1
    correct_answer: str

    @field_validator("text")
    @classmethod
    def text_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Question text cannot be empty")
        return v

    @field_validator("type")
    @classmethod
    def valid_type(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in VALID_QUESTION_TYPES:
            raise ValueError(
                f"Question type must be one of: {', '.join(sorted(VALID_QUESTION_TYPES))}"
            )
        return v

    @field_validator("options")
    @classmethod
    def at_least_two_options(cls, v: list[str]) -> list[str]:
        if len(v) < 2:
            raise ValueError("At least 2 options are required")
        return [opt.strip() for opt in v]

    @field_validator("marks")
    @classmethod
    def positive_marks(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Marks must be at least 1")
        return v

    @field_validator("correct_answer")
    @classmethod
    def answer_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Correct answer cannot be empty")
        return v


class CreateExamSchema(BaseModel):
    """POST /api/v1/exams"""

    title: str
    description: str = ""
    duration: int  # minutes
    questions: list[QuestionSchema]
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v or len(v) < 3:
            raise ValueError("Title must be at least 3 characters")
        return v

    @field_validator("duration")
    @classmethod
    def positive_duration(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Duration must be at least 1 minute")
        if v > 480:
            raise ValueError("Duration cannot exceed 480 minutes (8 hours)")
        return v

    @field_validator("questions")
    @classmethod
    def at_least_one_question(cls, v: list) -> list:
        if not v:
            raise ValueError("Exam must have at least 1 question")
        return v


class UpdateExamSchema(BaseModel):
    """PUT /api/v1/exams/<id>"""

    title: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[int] = None
    questions: Optional[list[QuestionSchema]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @field_validator("title")
    @classmethod
    def title_check(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) < 3:
                raise ValueError("Title must be at least 3 characters")
        return v

    @field_validator("duration")
    @classmethod
    def duration_check(cls, v):
        if v is not None and v < 1:
            raise ValueError("Duration must be at least 1 minute")
        return v
