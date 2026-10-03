"""
SecureAssess — Risk Engine Service.

Calculates a cumulative malpractice risk score based on
anti-cheating events recorded during an exam attempt.

IMPORTANT: A high risk score is NOT proof of cheating.
It is a review indicator for human examiners.
"""

from app.models.event_model import count_events_by_type


# ------------------------------------------------------------------
# Event weights (configurable)
# ------------------------------------------------------------------
EVENT_WEIGHTS: dict[str, int] = {
    "tab_switch": 10,
    "window_blur": 8,
    "fullscreen_exit": 12,
    "copy": 15,
    "paste": 15,
    "right_click": 5,
    "devtools_detected": 25,
    "camera_off": 12,
    "no_face": 10,
    "multiple_face": 20,
    "network_disconnect": 8,
    "ip_change": 20,
    "suspicious_answer_pattern": 15,
}

# ------------------------------------------------------------------
# Risk levels
# ------------------------------------------------------------------
RISK_LEVELS = [
    (0, 34, "low"),
    (35, 69, "medium"),
    (70, 100, "high"),
]


def _classify_risk(score: int) -> str:
    """Map a numeric score to a risk level label."""
    for low, high, label in RISK_LEVELS:
        if low <= score <= high:
            return label
    return "high"  # Anything above 100 (should not happen after capping)


def calculate_risk_score(attempt_id: str) -> tuple[int, str]:
    """
    Calculate the risk score for an attempt.

    Returns (score_capped_at_100, risk_level_string).
    """
    event_counts = count_events_by_type(attempt_id)

    total = 0
    for event_type, count in event_counts.items():
        weight = EVENT_WEIGHTS.get(event_type, 5)
        total += weight * count

    # Cap at 100
    capped = min(total, 100)
    level = _classify_risk(capped)

    return capped, level


def get_risk_breakdown(attempt_id: str) -> dict:
    """
    Return a detailed breakdown of the risk score.

    Useful for examiner review.
    """
    event_counts = count_events_by_type(attempt_id)

    breakdown = []
    total = 0
    for event_type, count in event_counts.items():
        weight = EVENT_WEIGHTS.get(event_type, 5)
        contribution = weight * count
        total += contribution
        breakdown.append({
            "event_type": event_type,
            "count": count,
            "weight": weight,
            "contribution": contribution,
        })

    capped = min(total, 100)
    level = _classify_risk(capped)

    return {
        "risk_score": capped,
        "risk_level": level,
        "raw_total": total,
        "breakdown": breakdown,
    }
