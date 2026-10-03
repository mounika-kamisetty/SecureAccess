"""
SecureAssess — Question Model.

Helpers for question serialisation and randomisation.
Questions are embedded inside exam documents.
"""

import random
import copy


def serialize_question(q: dict) -> dict:
    """Full question representation (for examiners/admin — includes correct_answer)."""
    return {
        "question_id": q.get("question_id", ""),
        "text": q["text"],
        "type": q.get("type", "mcq"),
        "options": q.get("options", []),
        "marks": q.get("marks", 1),
        "correct_answer": q.get("correct_answer"),
    }


def serialize_question_safe(q: dict) -> dict:
    """
    Student-safe question — correct_answer is NEVER included.

    This is the only serialiser used when serving questions to students.
    """
    return {
        "question_id": q.get("question_id", ""),
        "text": q["text"],
        "type": q.get("type", "mcq"),
        "options": q.get("options", []),
        "marks": q.get("marks", 1),
    }


def randomize_questions(questions: list[dict]) -> list[dict]:
    """
    Return a shuffled deep-copy of the questions list.

    Each student attempt gets a unique ordering, so no two students
    see the same question sequence.
    """
    shuffled = copy.deepcopy(questions)
    random.shuffle(shuffled)
    return shuffled


def get_answer_key(questions: list[dict]) -> dict[str, str]:
    """
    Build a mapping of question_id -> correct_answer.

    Used internally by the scoring engine — never exposed to clients.
    """
    return {
        q["question_id"]: q["correct_answer"]
        for q in questions
        if "correct_answer" in q
    }
