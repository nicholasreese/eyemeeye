"""End-to-end tests for authentication and role-protected flows."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Mapping
from unittest.mock import patch

from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from src.app.models import Role, User


def _register_user(
    client: FlaskClient,
    username: str,
    role: Role = Role.USER,
    overrides: Mapping[str, str] | None = None,
) -> User:
    """Registers a user and verifies their email address."""
    payload = {
        "username": username,
        "email": f"{username}@example.com",
        "phone_number": "1234567890",
        "imei": "12345678901234",
        "password": "Test@1234",
        "role": role.value,
    }
    if overrides:
        payload.update(overrides)
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201

    with client.application.app_context():
        user: User = User.query.filter_by(username=username).one()
        token = user.email_verification_token

    assert token is not None
    verify_response = client.get(f"/api/auth/verify-email?token={token}")
    assert verify_response.status_code == 200

    with client.application.app_context():
        return User.query.filter_by(username=username).one()


def _login_user(client: FlaskClient, username: str) -> None:
    """Performs the full two-step login: password check then OTP verification."""
    with patch("src.app.services.auth.send_login_otp") as mock_send:
        response: TestResponse = client.post(
            "/api/auth/login",
            json={"username": username, "password": "Test@1234"},
        )
        assert response.status_code == 202
        assert response.get_json()["requires_otp"] is True
        captured_otp: str = mock_send.call_args[0][1]

    response = client.post(
        "/api/auth/verify-otp",
        json={"username": username, "otp": captured_otp},
    )
    assert response.status_code == 200


def test_register_and_login_flow(client: FlaskClient) -> None:
    _register_user(client, "testuser")
    _login_user(client, "testuser")


def test_update_phone_status(client: FlaskClient) -> None:
    _register_user(client, "statususer")
    _login_user(client, "statususer")
    response: TestResponse = client.post("/api/users/status", json={"status": "online"})
    assert response.status_code == 200


def test_register_missing_fields_returns_validation_error(client: FlaskClient) -> None:
    response: TestResponse = client.post(
        "/api/auth/register",
        json={"username": "baduser"},
    )
    assert response.status_code == 400
    payload = response.get_json()
    assert "Missing required fields" in payload["message"]


def test_register_invalid_email_returns_validation_error(client: FlaskClient) -> None:
    response: TestResponse = client.post(
        "/api/auth/register",
        json={
            "username": "bademail",
            "email": "invalid",
            "phone_number": "1234567890",
            "imei": "12345678901234",
            "password": "Test@1234",
        },
    )
    assert response.status_code == 400
    payload = response.get_json()
    assert "email" in payload["message"]


def test_login_missing_password_returns_validation_error(client: FlaskClient) -> None:
    response: TestResponse = client.post(
        "/api/auth/login",
        json={"username": "user"},
    )
    assert response.status_code == 400
    payload = response.get_json()
    assert "Missing required fields" in payload["message"]


def test_login_blocked_without_email_verification(client: FlaskClient) -> None:
    """Login must be rejected when the user has not verified their email."""
    client.post(
        "/api/auth/register",
        json={
            "username": "unverified",
            "email": "unverified@example.com",
            "phone_number": "1234567890",
            "imei": "12345678901234",
            "password": "Test@1234",
        },
    )
    response: TestResponse = client.post(
        "/api/auth/login",
        json={"username": "unverified", "password": "Test@1234"},
    )
    assert response.status_code == 403
    assert "verif" in response.get_json()["message"].lower()


def test_verify_email_with_invalid_token_returns_error(client: FlaskClient) -> None:
    response: TestResponse = client.get("/api/auth/verify-email?token=notavalidtoken")
    assert response.status_code == 400


def test_verify_email_with_no_token_returns_error(client: FlaskClient) -> None:
    response: TestResponse = client.get("/api/auth/verify-email")
    assert response.status_code == 400


def test_login_returns_202_with_requires_otp(client: FlaskClient) -> None:
    _register_user(client, "otpuser")
    with patch("src.app.services.auth.send_login_otp"):
        response: TestResponse = client.post(
            "/api/auth/login",
            json={"username": "otpuser", "password": "Test@1234"},
        )
    assert response.status_code == 202
    data = response.get_json()
    assert data["requires_otp"] is True


def test_verify_otp_with_invalid_code_returns_error(client: FlaskClient) -> None:
    _register_user(client, "badotpuser")
    with patch("src.app.services.auth.send_login_otp"):
        client.post(
            "/api/auth/login",
            json={"username": "badotpuser", "password": "Test@1234"},
        )
    response: TestResponse = client.post(
        "/api/auth/verify-otp",
        json={"username": "badotpuser", "otp": "000000"},
    )
    assert response.status_code == 401


def test_verify_otp_with_expired_code_returns_error(client: FlaskClient) -> None:
    _register_user(client, "expiredotp")
    with patch("src.app.utils.email.send_login_otp"):
        client.post(
            "/api/auth/login",
            json={"username": "expiredotp", "password": "Test@1234"},
        )

    with client.application.app_context():
        from src.app.extensions import db

        user = User.query.filter_by(username="expiredotp").one()
        user.otp_expires_at = datetime.utcnow() - timedelta(minutes=1)
        db.session.commit()

    response: TestResponse = client.post(
        "/api/auth/verify-otp",
        json={"username": "expiredotp", "otp": "123456"},
    )
    assert response.status_code == 401
    assert "expired" in response.get_json()["message"].lower()


def test_verify_otp_with_non_numeric_code_returns_validation_error(
    client: FlaskClient,
) -> None:
    response: TestResponse = client.post(
        "/api/auth/verify-otp",
        json={"username": "someone", "otp": "abcdef"},
    )
    assert response.status_code == 400
    assert "otp" in response.get_json()["message"].lower()


def test_manager_cannot_be_accessed_by_regular_user(client: FlaskClient) -> None:
    _register_user(client, "regular")
    _login_user(client, "regular")
    response: TestResponse = client.get("/api/manager/users")
    assert response.status_code == 403


def test_admin_can_list_users(client: FlaskClient) -> None:
    _register_user(client, "admin", role=Role.ADMIN)
    _login_user(client, "admin")
    response: TestResponse = client.get("/api/manager/users")
    assert response.status_code == 200
    payload: dict[str, Any] = response.get_json()
    assert "users" in payload
