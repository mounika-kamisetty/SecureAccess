"""
SecureAssess — Exam Tests.

Covers: creation, update, publish, student access (correct_answer stripped),
role authorization.
"""
# pyrefly: ignore [missing-import]
import pytest

from tests.conftest import _auth_header


class TestExamCreation:
    """Exam CRUD tests."""

    def test_create_exam_as_examiner(self, client, examiner_token, sample_exam_data):
        resp = client.post(
            "/api/v1/exams",
            json=sample_exam_data,
            headers=_auth_header(examiner_token),
        )
        assert resp.status_code == 201
        exam = resp.get_json()["data"]["exam"]
        assert exam["title"] == "Python Fundamentals"
        assert exam["status"] == "draft"
        assert len(exam["questions"]) == 5
        assert exam["total_marks"] == 25

    def test_create_exam_as_student_forbidden(self, client, student_token, sample_exam_data):
        resp = client.post(
            "/api/v1/exams",
            json=sample_exam_data,
            headers=_auth_header(student_token),
        )
        assert resp.status_code == 403

    def test_create_exam_no_auth(self, client, sample_exam_data):
        resp = client.post("/api/v1/exams", json=sample_exam_data)
        assert resp.status_code == 401


class TestExamPublish:
    """Publishing tests."""

    def test_publish_exam(self, client, examiner_token, sample_exam_data):
        # Create
        create_resp = client.post(
            "/api/v1/exams", json=sample_exam_data,
            headers=_auth_header(examiner_token),
        )
        exam_id = create_resp.get_json()["data"]["exam"]["id"]

        # Publish
        resp = client.patch(
            f"/api/v1/exams/{exam_id}/publish",
            headers=_auth_header(examiner_token),
        )
        assert resp.status_code == 200
        assert resp.get_json()["data"]["exam"]["status"] == "published"

    def test_publish_already_published(self, client, examiner_token, sample_exam_data):
        create_resp = client.post(
            "/api/v1/exams", json=sample_exam_data,
            headers=_auth_header(examiner_token),
        )
        exam_id = create_resp.get_json()["data"]["exam"]["id"]

        # Publish once
        client.patch(
            f"/api/v1/exams/{exam_id}/publish",
            headers=_auth_header(examiner_token),
        )
        # Try again
        resp = client.patch(
            f"/api/v1/exams/{exam_id}/publish",
            headers=_auth_header(examiner_token),
        )
        assert resp.status_code == 400


class TestCorrectAnswerProtection:
    """CRITICAL: correct_answer must NEVER be returned to students."""

    def test_student_cannot_see_correct_answers(
        self, client, examiner_token, student_token, sample_exam_data
    ):
        # Create & publish as examiner
        create_resp = client.post(
            "/api/v1/exams", json=sample_exam_data,
            headers=_auth_header(examiner_token),
        )
        exam_id = create_resp.get_json()["data"]["exam"]["id"]
        client.patch(
            f"/api/v1/exams/{exam_id}/publish",
            headers=_auth_header(examiner_token),
        )

        # Fetch as student
        resp = client.get(
            f"/api/v1/exams/{exam_id}",
            headers=_auth_header(student_token),
        )
        assert resp.status_code == 200
        exam = resp.get_json()["data"]["exam"]

        for q in exam["questions"]:
            assert "correct_answer" not in q, (
                f"correct_answer leaked to student for question: {q['text']}"
            )

    def test_examiner_can_see_correct_answers(
        self, client, examiner_token, sample_exam_data
    ):
        create_resp = client.post(
            "/api/v1/exams", json=sample_exam_data,
            headers=_auth_header(examiner_token),
        )
        exam_id = create_resp.get_json()["data"]["exam"]["id"]

        resp = client.get(
            f"/api/v1/exams/{exam_id}",
            headers=_auth_header(examiner_token),
        )
        exam = resp.get_json()["data"]["exam"]
        for q in exam["questions"]:
            assert "correct_answer" in q


class TestExamList:
    """List exams with role-based filtering."""

    def test_student_only_sees_published(
        self, client, examiner_token, student_token, sample_exam_data
    ):
        # Create a draft exam
        client.post(
            "/api/v1/exams", json=sample_exam_data,
            headers=_auth_header(examiner_token),
        )

        # Student should see zero (draft not visible)
        resp = client.get("/api/v1/exams", headers=_auth_header(student_token))
        assert resp.status_code == 200
        assert resp.get_json()["data"]["total"] == 0
