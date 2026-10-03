"""
SecureAssess — Attempt Tests.

Covers: start attempt, save answer, submit, double submission prevention,
unauthorized access, server-side scoring.
"""
# pyrefly: ignore [missing-import]
import pytest

from tests.conftest import _register, _login, _auth_header


def _create_published_exam(client, examiner_token, sample_exam_data):
    """Helper: create and publish an exam, return its ID."""
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


class TestStartAttempt:
    """Starting exam attempts."""

    def test_start_attempt_success(
        self, client, examiner_token, student_token, sample_exam_data
    ):
        exam_id = _create_published_exam(client, examiner_token, sample_exam_data)

        resp = client.post(
            "/api/v1/attempts/start",
            json={"exam_id": exam_id},
            headers=_auth_header(student_token),
        )
        assert resp.status_code == 201
        attempt = resp.get_json()["data"]["attempt"]
        assert attempt["status"] == "in_progress"
        assert attempt["exam_id"] == exam_id
        assert len(attempt["question_order"]) == 5

    def test_start_attempt_on_draft_exam(
        self, client, examiner_token, student_token, sample_exam_data
    ):
        # Create but don't publish
        create_resp = client.post(
            "/api/v1/exams", json=sample_exam_data,
            headers=_auth_header(examiner_token),
        )
        exam_id = create_resp.get_json()["data"]["exam"]["id"]

        resp = client.post(
            "/api/v1/attempts/start",
            json={"exam_id": exam_id},
            headers=_auth_header(student_token),
        )
        assert resp.status_code == 400

    def test_duplicate_active_attempt(
        self, client, examiner_token, student_token, sample_exam_data
    ):
        exam_id = _create_published_exam(client, examiner_token, sample_exam_data)

        # First attempt
        client.post(
            "/api/v1/attempts/start",
            json={"exam_id": exam_id},
            headers=_auth_header(student_token),
        )
        # Second attempt should return the existing one, not create a new one
        resp = client.post(
            "/api/v1/attempts/start",
            json={"exam_id": exam_id},
            headers=_auth_header(student_token),
        )
        assert resp.status_code == 201  # Returns existing attempt

    def test_examiner_cannot_start_attempt(
        self, client, examiner_token, sample_exam_data
    ):
        exam_id = _create_published_exam(client, examiner_token, sample_exam_data)
        resp = client.post(
            "/api/v1/attempts/start",
            json={"exam_id": exam_id},
            headers=_auth_header(examiner_token),
        )
        assert resp.status_code == 403


class TestSaveAnswer:
    """Answer saving tests."""

    def test_save_answer_success(
        self, client, examiner_token, student_token, sample_exam_data
    ):
        exam_id = _create_published_exam(client, examiner_token, sample_exam_data)

        start_resp = client.post(
            "/api/v1/attempts/start",
            json={"exam_id": exam_id},
            headers=_auth_header(student_token),
        )
        attempt = start_resp.get_json()["data"]["attempt"]
        attempt_id = attempt["id"]
        qid = attempt["question_order"][0]

        resp = client.put(
            f"/api/v1/attempts/{attempt_id}/answer",
            json={"question_id": qid, "answer": "8"},
            headers=_auth_header(student_token),
        )
        assert resp.status_code == 200

    def test_save_answer_wrong_question(
        self, client, examiner_token, student_token, sample_exam_data
    ):
        exam_id = _create_published_exam(client, examiner_token, sample_exam_data)

        start_resp = client.post(
            "/api/v1/attempts/start",
            json={"exam_id": exam_id},
            headers=_auth_header(student_token),
        )
        attempt_id = start_resp.get_json()["data"]["attempt"]["id"]

        resp = client.put(
            f"/api/v1/attempts/{attempt_id}/answer",
            json={"question_id": "nonexistent_q", "answer": "x"},
            headers=_auth_header(student_token),
        )
        assert resp.status_code == 400


class TestUnauthorizedAttemptAccess:
    """IDOR protection tests."""

    def test_other_student_cannot_access_attempt(
        self, client, examiner_token, student_token, sample_exam_data
    ):
        exam_id = _create_published_exam(client, examiner_token, sample_exam_data)

        # Student 1 starts an attempt
        start_resp = client.post(
            "/api/v1/attempts/start",
            json={"exam_id": exam_id},
            headers=_auth_header(student_token),
        )
        attempt_id = start_resp.get_json()["data"]["attempt"]["id"]

        # Register student 2
        _register(client, "Student2", "student2@test.com", "Pass@1234", "student")
        login_resp = _login(client, "student2@test.com", "Pass@1234")
        token2 = login_resp.get_json()["data"]["access_token"]

        # Student 2 tries to save answer on student 1's attempt
        resp = client.put(
            f"/api/v1/attempts/{attempt_id}/answer",
            json={"question_id": "q_fake", "answer": "x"},
            headers=_auth_header(token2),
        )
        assert resp.status_code == 403


class TestSubmission:
    """Submission and scoring tests."""

    def test_submit_scores_correctly(
        self, client, examiner_token, student_token, sample_exam_data
    ):
        exam_id = _create_published_exam(client, examiner_token, sample_exam_data)

        # Start attempt
        start_resp = client.post(
            "/api/v1/attempts/start",
            json={"exam_id": exam_id},
            headers=_auth_header(student_token),
        )
        attempt = start_resp.get_json()["data"]["attempt"]
        attempt_id = attempt["id"]

        # Get exam to know question IDs (fetch as examiner to get correct_answer)
        exam_resp = client.get(
            f"/api/v1/exams/{exam_id}",
            headers=_auth_header(examiner_token),
        )
        questions = exam_resp.get_json()["data"]["exam"]["questions"]

        # Answer all questions correctly
        for q in questions:
            client.put(
                f"/api/v1/attempts/{attempt_id}/answer",
                json={"question_id": q["question_id"], "answer": q["correct_answer"]},
                headers=_auth_header(student_token),
            )

        # Submit
        resp = client.post(
            f"/api/v1/attempts/{attempt_id}/submit",
            headers=_auth_header(student_token),
        )
        assert resp.status_code == 200
        result = resp.get_json()["data"]["result"]
        assert result["score"] == 25
        assert result["max_score"] == 25
        assert result["percentage"] == 100.0
        assert result["status"] == "submitted"

    def test_double_submission_prevented(
        self, client, examiner_token, student_token, sample_exam_data
    ):
        exam_id = _create_published_exam(client, examiner_token, sample_exam_data)

        start_resp = client.post(
            "/api/v1/attempts/start",
            json={"exam_id": exam_id},
            headers=_auth_header(student_token),
        )
        attempt_id = start_resp.get_json()["data"]["attempt"]["id"]

        # First submit
        client.post(
            f"/api/v1/attempts/{attempt_id}/submit",
            headers=_auth_header(student_token),
        )
        # Second submit
        resp = client.post(
            f"/api/v1/attempts/{attempt_id}/submit",
            headers=_auth_header(student_token),
        )
        assert resp.status_code == 400
        assert "already" in resp.get_json()["message"].lower()

    def test_cannot_save_after_submission(
        self, client, examiner_token, student_token, sample_exam_data
    ):
        exam_id = _create_published_exam(client, examiner_token, sample_exam_data)

        start_resp = client.post(
            "/api/v1/attempts/start",
            json={"exam_id": exam_id},
            headers=_auth_header(student_token),
        )
        attempt = start_resp.get_json()["data"]["attempt"]
        attempt_id = attempt["id"]
        qid = attempt["question_order"][0]

        # Submit
        client.post(
            f"/api/v1/attempts/{attempt_id}/submit",
            headers=_auth_header(student_token),
        )

        # Try to save after submission
        resp = client.put(
            f"/api/v1/attempts/{attempt_id}/answer",
            json={"question_id": qid, "answer": "sneaky"},
            headers=_auth_header(student_token),
        )
        assert resp.status_code == 400


class TestMyAttempts:
    """Student attempt history."""

    def test_my_attempts(
        self, client, examiner_token, student_token, sample_exam_data
    ):
        exam_id = _create_published_exam(client, examiner_token, sample_exam_data)

        client.post(
            "/api/v1/attempts/start",
            json={"exam_id": exam_id},
            headers=_auth_header(student_token),
        )

        resp = client.get("/api/v1/attempts/my", headers=_auth_header(student_token))
        assert resp.status_code == 200
        assert resp.get_json()["data"]["total"] >= 1
