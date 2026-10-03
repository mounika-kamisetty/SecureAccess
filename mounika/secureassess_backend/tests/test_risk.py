"""
SecureAssess — Risk Engine Tests.

Covers: event recording, risk calculation, score capping, risk levels.
"""
# pyrefly: ignore [missing-import]
import pytest

from tests.conftest import _register, _login, _auth_header


def _create_published_exam(client, examiner_token, sample_exam_data):
    create_resp = client.post(
        "/api/v1/exams", json=sample_exam_data,
        headers=_auth_header(examiner_token),
    )
    exam_id = create_resp.get_json()["data"]["exam"]["id"]
    client.patch(
        f"/api/v1/exams/{exam_id}/publish",
        headers=_auth_header(examiner_token),
    )
    return exam_id


class TestEventRecording:
    """Event recording tests."""

    def test_record_event(
        self, client, examiner_token, student_token, sample_exam_data
    ):
        exam_id = _create_published_exam(client, examiner_token, sample_exam_data)

        start_resp = client.post(
            "/api/v1/attempts/start",
            json={"exam_id": exam_id},
            headers=_auth_header(student_token),
        )
        attempt_id = start_resp.get_json()["data"]["attempt"]["id"]

        resp = client.post(
            "/api/v1/events",
            json={"attempt_id": attempt_id, "event_type": "tab_switch"},
            headers=_auth_header(student_token),
        )
        assert resp.status_code == 201
        assert resp.get_json()["data"]["event"]["event_type"] == "tab_switch"

    def test_invalid_event_type(
        self, client, examiner_token, student_token, sample_exam_data
    ):
        exam_id = _create_published_exam(client, examiner_token, sample_exam_data)

        start_resp = client.post(
            "/api/v1/attempts/start",
            json={"exam_id": exam_id},
            headers=_auth_header(student_token),
        )
        attempt_id = start_resp.get_json()["data"]["attempt"]["id"]

        resp = client.post(
            "/api/v1/events",
            json={"attempt_id": attempt_id, "event_type": "hacking"},
            headers=_auth_header(student_token),
        )
        assert resp.status_code == 422


class TestRiskCalculation:
    """Risk score calculation tests."""

    def test_risk_score_after_events(
        self, client, examiner_token, student_token, sample_exam_data
    ):
        exam_id = _create_published_exam(client, examiner_token, sample_exam_data)

        start_resp = client.post(
            "/api/v1/attempts/start",
            json={"exam_id": exam_id},
            headers=_auth_header(student_token),
        )
        attempt_id = start_resp.get_json()["data"]["attempt"]["id"]

        # Record some events
        for _ in range(3):
            client.post(
                "/api/v1/events",
                json={"attempt_id": attempt_id, "event_type": "tab_switch"},
                headers=_auth_header(student_token),
            )

        # Submit and check risk
        resp = client.post(
            f"/api/v1/attempts/{attempt_id}/submit",
            headers=_auth_header(student_token),
        )
        result = resp.get_json()["data"]["result"]
        # 3 × tab_switch (weight 10) = 30 → risk_level = "low"
        assert result["risk_score"] == 30
        assert result["risk_level"] == "low"

    def test_risk_score_capped_at_100(
        self, client, examiner_token, student_token, sample_exam_data
    ):
        exam_id = _create_published_exam(client, examiner_token, sample_exam_data)

        start_resp = client.post(
            "/api/v1/attempts/start",
            json={"exam_id": exam_id},
            headers=_auth_header(student_token),
        )
        attempt_id = start_resp.get_json()["data"]["attempt"]["id"]

        # Flood events: 10 × devtools_detected (weight 25) = 250 → capped at 100
        for _ in range(10):
            client.post(
                "/api/v1/events",
                json={"attempt_id": attempt_id, "event_type": "devtools_detected"},
                headers=_auth_header(student_token),
            )

        resp = client.post(
            f"/api/v1/attempts/{attempt_id}/submit",
            headers=_auth_header(student_token),
        )
        result = resp.get_json()["data"]["result"]
        assert result["risk_score"] == 100
        assert result["risk_level"] == "high"


class TestRiskBreakdown:
    """Examiner risk breakdown view."""

    def test_examiner_views_risk_breakdown(
        self, client, examiner_token, student_token, sample_exam_data
    ):
        exam_id = _create_published_exam(client, examiner_token, sample_exam_data)

        start_resp = client.post(
            "/api/v1/attempts/start",
            json={"exam_id": exam_id},
            headers=_auth_header(student_token),
        )
        attempt_id = start_resp.get_json()["data"]["attempt"]["id"]

        client.post(
            "/api/v1/events",
            json={"attempt_id": attempt_id, "event_type": "copy"},
            headers=_auth_header(student_token),
        )

        resp = client.get(
            f"/api/v1/events/{attempt_id}",
            headers=_auth_header(examiner_token),
        )
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert len(data["events"]) >= 1
        assert "risk" in data
        assert data["risk"]["risk_score"] >= 0
