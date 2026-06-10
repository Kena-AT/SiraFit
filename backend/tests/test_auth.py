"""
Auth endpoint tests — covers registration, login, token refresh,
logout, forgot/reset password, and email verification flows.
"""


class TestRegister:
    def test_register_success(self, client):
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "Password123!",
                "full_name": "New User",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "newuser@example.com"
        assert "id" in data
        assert "hashed_password" not in data  # never leak password hash

    def test_register_duplicate_email(self, client):
        # Register once
        client.post(
            "/api/v1/auth/register",
            json={"email": "dup@example.com", "password": "Password123!"},
        )
        # Register again with same email
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": "dup@example.com", "password": "Password123!"},
        )
        assert resp.status_code == 400
        assert "already exists" in resp.json()["detail"]

    def test_register_invalid_email(self, client):
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "password": "Password123!"},
        )
        assert resp.status_code == 422  # Pydantic validation error


class TestLogin:
    def test_login_success(self, client, registered_user):
        resp = client.post(
            "/api/v1/auth/login",
            data={"username": "fixture@example.com", "password": "Password123!"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, registered_user):
        resp = client.post(
            "/api/v1/auth/login",
            data={"username": "fixture@example.com", "password": "WrongPass!"},
        )
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client):
        resp = client.post(
            "/api/v1/auth/login",
            data={"username": "ghost@example.com", "password": "Password123!"},
        )
        assert resp.status_code == 401


class TestUserProfile:
    def test_get_me_authenticated(self, client, auth_tokens):
        resp = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "fixture@example.com"

    def test_get_me_unauthenticated(self, client):
        resp = client.get("/api/v1/users/me")
        assert resp.status_code == 401

    def test_get_me_invalid_token(self, client):
        resp = client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer this.is.not.a.valid.token"},
        )
        assert resp.status_code == 401


class TestRefreshToken:
    def test_refresh_token_success(self, client, auth_tokens):
        resp = client.post(
            "/api/v1/auth/refresh-token",
            json={"refresh_token": auth_tokens["refresh_token"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_with_access_token_fails(self, client, auth_tokens):
        resp = client.post(
            "/api/v1/auth/refresh-token",
            json={"refresh_token": auth_tokens["access_token"]},  # wrong type
        )
        assert resp.status_code == 400


class TestForgotResetPassword:
    def test_forgot_password_existing_email(self, client, registered_user):
        resp = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "fixture@example.com"},
        )
        assert resp.status_code == 200
        # Should not reveal whether the user exists
        assert "reset link" in resp.json()["message"].lower()

    def test_forgot_password_nonexistent_email(self, client):
        resp = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "nobody@example.com"},
        )
        # Must return 200 to prevent email enumeration
        assert resp.status_code == 200

    def test_reset_password_invalid_token(self, client):
        resp = client.post(
            "/api/v1/auth/reset-password",
            json={"token": "invalid.token.here", "new_password": "NewPassword123!"},
        )
        assert resp.status_code == 400


class TestLogout:
    def test_logout_success(self, client, auth_tokens):
        resp = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": auth_tokens["refresh_token"]},
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "Logged out successfully"
