"""
SecureAssess — Authentication Tests.

Covers: registration, duplicate registration, login, invalid login,
JWT protection, refresh, logout, password change.
"""
# pyrefly: ignore [missing-import]
import pytest

from tests.conftest import _register, _login, _auth_header


class TestRegistration:
    """Registration endpoint tests."""

    def test_register_success(self, client):
        resp = _register(client, "Alice", "alice@test.com", "Pass@1234", "student")
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["user"]["email"] == "alice@test.com"
        assert data["data"]["user"]["role"] == "student"

    def test_register_duplicate_email(self, client):
        _register(client, "Alice", "alice@test.com", "Pass@1234")
        resp = _register(client, "Alice2", "alice@test.com", "Pass@1234")
        assert resp.status_code == 409
        assert resp.get_json()["success"] is False

    def test_register_weak_password(self, client):
        resp = _register(client, "Bob", "bob@test.com", "weak")
        assert resp.status_code == 422

    def test_register_invalid_role(self, client):
        resp = _register(client, "Eve", "eve@test.com", "Pass@1234", "superadmin")
        assert resp.status_code == 422

    def test_register_missing_fields(self, client):
        resp = client.post("/api/v1/auth/register", json={"email": "x@x.com"})
        assert resp.status_code == 422

    def test_password_not_in_response(self, client):
        resp = _register(client, "Safe", "safe@test.com", "Pass@1234")
        data = resp.get_json()
        user = data["data"]["user"]
        assert "password" not in user
        assert "password_hash" not in user


class TestLogin:
    """Login endpoint tests."""

    def test_login_success(self, client):
        _register(client, "Alice", "alice@test.com", "Pass@1234")
        resp = _login(client, "alice@test.com", "Pass@1234")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert data["data"]["user"]["email"] == "alice@test.com"

    def test_login_wrong_password(self, client):
        _register(client, "Alice", "alice@test.com", "Pass@1234")
        resp = _login(client, "alice@test.com", "WrongPass@1")
        assert resp.status_code == 401

    def test_login_nonexistent_email(self, client):
        resp = _login(client, "nobody@test.com", "Pass@1234")
        assert resp.status_code == 401

    def test_login_email_case_insensitive(self, client):
        _register(client, "Alice", "alice@test.com", "Pass@1234")
        resp = _login(client, "Alice@Test.COM", "Pass@1234")
        assert resp.status_code == 200


class TestJWTProtection:
    """JWT-protected endpoint tests."""

    def test_access_protected_without_token(self, client):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_access_protected_with_invalid_token(self, client):
        resp = client.get("/api/v1/auth/me", headers=_auth_header("invalid.token.here"))
        assert resp.status_code in [401, 422]

    def test_access_protected_with_valid_token(self, client, student_token):
        resp = client.get("/api/v1/auth/me", headers=_auth_header(student_token))
        assert resp.status_code == 200
        assert resp.get_json()["data"]["user"]["role"] == "student"


class TestRefreshToken:
    """Token refresh tests."""

    def test_refresh_success(self, client):
        _register(client, "Alice", "alice@test.com", "Pass@1234")
        login_resp = _login(client, "alice@test.com", "Pass@1234")
        refresh_token = login_resp.get_json()["data"]["refresh_token"]

        resp = client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert resp.status_code == 200
        assert "access_token" in resp.get_json()["data"]

    def test_refresh_with_invalid_token(self, client):
        resp = client.post("/api/v1/auth/refresh", json={
            "refresh_token": "bad.token",
        })
        assert resp.status_code == 401


class TestLogout:
    """Logout / token revocation tests."""

    def test_logout_revokes_refresh(self, client):
        _register(client, "Alice", "alice@test.com", "Pass@1234")
        login_resp = _login(client, "alice@test.com", "Pass@1234")
        refresh_token = login_resp.get_json()["data"]["refresh_token"]

        # Logout
        resp = client.post("/api/v1/auth/logout", json={
            "refresh_token": refresh_token,
        })
        assert resp.status_code == 200

        # Refresh should now fail
        resp2 = client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert resp2.status_code == 401


class TestChangePassword:
    """Password change tests."""

    def test_change_password_success(self, client, student_token):
        resp = client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "Pass@1234",
                "new_password": "NewPass@5678",
            },
            headers=_auth_header(student_token),
        )
        assert resp.status_code == 200

        # Old password should no longer work
        resp2 = _login(client, "student@test.com", "Pass@1234")
        assert resp2.status_code == 401

        # New password should work
        resp3 = _login(client, "student@test.com", "NewPass@5678")
        assert resp3.status_code == 200

    def test_change_password_wrong_current(self, client, student_token):
        resp = client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "WrongPass@1",
                "new_password": "NewPass@5678",
            },
            headers=_auth_header(student_token),
        )
        assert resp.status_code == 400
