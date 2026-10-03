"""
SecureAssess — Admin & Authorisation Tests.

Covers: admin-only endpoints, role enforcement, user management.
"""

# pyrefly: ignore [missing-import]
import pytest

from tests.conftest import _auth_header


class TestAdminAuthorization:
    """Only admin can access admin endpoints."""

    def test_student_cannot_access_stats(self, client, student_token):
        resp = client.get("/api/v1/admin/stats", headers=_auth_header(student_token))
        assert resp.status_code == 403

    def test_examiner_cannot_access_stats(self, client, examiner_token):
        resp = client.get("/api/v1/admin/stats", headers=_auth_header(examiner_token))
        assert resp.status_code == 403

    def test_admin_can_access_stats(self, client, admin_token):
        resp = client.get("/api/v1/admin/stats", headers=_auth_header(admin_token))
        assert resp.status_code == 200
        stats = resp.get_json()["data"]["stats"]
        assert "users" in stats
        assert "exams" in stats
        assert "attempts" in stats


class TestAdminAuditLogs:
    """Audit log access."""

    def test_admin_can_view_audit_logs(self, client, admin_token):
        resp = client.get("/api/v1/admin/audit-logs", headers=_auth_header(admin_token))
        assert resp.status_code == 200
        assert "logs" in resp.get_json()["data"]

    def test_student_cannot_view_audit_logs(self, client, student_token):
        resp = client.get("/api/v1/admin/audit-logs", headers=_auth_header(student_token))
        assert resp.status_code == 403


class TestUserManagement:
    """Admin user management."""

    def test_admin_can_list_users(self, client, admin_token):
        resp = client.get("/api/v1/users", headers=_auth_header(admin_token))
        assert resp.status_code == 200
        assert "users" in resp.get_json()["data"]

    def test_student_cannot_list_users(self, client, student_token):
        resp = client.get("/api/v1/users", headers=_auth_header(student_token))
        assert resp.status_code == 403

    def test_admin_can_suspend_user(self, client, admin_token, student_token):
        # Get student user ID
        me_resp = client.get("/api/v1/auth/me", headers=_auth_header(student_token))
        student_id = me_resp.get_json()["data"]["user"]["id"]

        # Suspend
        resp = client.delete(
            f"/api/v1/users/{student_id}",
            headers=_auth_header(admin_token),
        )
        assert resp.status_code == 200
        assert "suspended" in resp.get_json()["message"].lower()

    def test_admin_cannot_suspend_self(self, client, admin_token):
        me_resp = client.get("/api/v1/auth/me", headers=_auth_header(admin_token))
        admin_id = me_resp.get_json()["data"]["user"]["id"]

        resp = client.delete(
            f"/api/v1/users/{admin_id}",
            headers=_auth_header(admin_token),
        )
        assert resp.status_code == 403


class TestRoleEscalation:
    """Prevent privilege escalation."""

    def test_student_cannot_create_exam(self, client, student_token):
        resp = client.post(
            "/api/v1/exams",
            json={"title": "Hack", "duration": 10, "questions": []},
            headers=_auth_header(student_token),
        )
        assert resp.status_code == 403

    def test_examiner_cannot_access_admin_stats(self, client, examiner_token):
        resp = client.get("/api/v1/admin/stats", headers=_auth_header(examiner_token))
        assert resp.status_code == 403

    def test_examiner_cannot_manage_users(self, client, examiner_token):
        resp = client.get("/api/v1/users", headers=_auth_header(examiner_token))
        assert resp.status_code == 403
