"""Tests for the forgot-password / reset-password flow."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from src.app.extensions import db
from src.app.models import User


def _register_and_verify(client: FlaskClient, username: str) -> User:
    """Registers a user and verifies their email, returning the User object."""

    client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "phone_number": "1234567890",
            "imei": "12345678901234",
            "password": "Test@1234",
        },
    )
    with client.application.app_context():
        user: User = User.query.filter_by(username=username).one()
        token = user.email_verification_token
    client.get(f"/api/auth/verify-email?token={token}")
    with client.application.app_context():
        return User.query.filter_by(username=username).one()


# ── POST /api/auth/forgot-password ───────────────────────────────────────────


def test_forgot_password_with_registered_email_sends_email(client: FlaskClient) -> None:
    _register_and_verify(client, "resetuser1")
    with patch("src.app.services.auth.send_password_reset_email") as mock_send:
        response: TestResponse = client.post(
            "/api/auth/forgot-password",
            json={"email": "resetuser1@example.com"},
        )
    assert response.status_code == 200
    mock_send.assert_called_once()
    assert "reset" in response.get_json()["message"].lower()


def test_forgot_password_with_unknown_email_returns_200_without_sending(
    client: FlaskClient,
) -> None:
    with patch("src.app.services.auth.send_password_reset_email") as mock_send:
        response: TestResponse = client.post(
            "/api/auth/forgot-password",
            json={"email": "nobody@example.com"},
        )
    assert response.status_code == 200
    mock_send.assert_not_called()


def test_forgot_password_with_invalid_email_returns_400(client: FlaskClient) -> None:
    response: TestResponse = client.post(
        "/api/auth/forgot-password",
        json={"email": "notanemail"},
    )
    assert response.status_code == 400


def test_forgot_password_missing_email_returns_400(client: FlaskClient) -> None:
    response: TestResponse = client.post("/api/auth/forgot-password", json={})
    assert response.status_code == 400


def test_forgot_password_stores_token_on_user(client: FlaskClient) -> None:
    _register_and_verify(client, "resetuser2")
    with patch("src.app.services.auth.send_password_reset_email"):
        client.post(
            "/api/auth/forgot-password",
            json={"email": "resetuser2@example.com"},
        )
    with client.application.app_context():
        user = User.query.filter_by(username="resetuser2").one()
        assert user.password_reset_token is not None
        assert user.password_reset_expires_at is not None


# ── POST /api/auth/reset-password ────────────────────────────────────────────


def test_reset_password_with_valid_token_succeeds(client: FlaskClient) -> None:
    _register_and_verify(client, "resetuser3")
    with patch("src.app.services.auth.send_password_reset_email") as mock_send:
        client.post(
            "/api/auth/forgot-password",
            json={"email": "resetuser3@example.com"},
        )
        captured_token: str = mock_send.call_args[0][1]

    response: TestResponse = client.post(
        "/api/auth/reset-password",
        json={"token": captured_token, "new_password": "NewPass@9999"},
    )
    assert response.status_code == 200
    assert "success" in response.get_json()["message"].lower()


def test_reset_password_clears_token_after_use(client: FlaskClient) -> None:
    _register_and_verify(client, "resetuser4")
    with patch("src.app.services.auth.send_password_reset_email") as mock_send:
        client.post(
            "/api/auth/forgot-password",
            json={"email": "resetuser4@example.com"},
        )
        captured_token: str = mock_send.call_args[0][1]

    client.post(
        "/api/auth/reset-password",
        json={"token": captured_token, "new_password": "NewPass@9999"},
    )
    with client.application.app_context():
        user = User.query.filter_by(username="resetuser4").one()
        assert user.password_reset_token is None
        assert user.password_reset_expires_at is None


def test_reset_password_with_invalid_token_returns_400(client: FlaskClient) -> None:
    response: TestResponse = client.post(
        "/api/auth/reset-password",
        json={"token": "notavalidtoken", "new_password": "NewPass@9999"},
    )
    assert response.status_code == 400


def test_reset_password_with_expired_token_returns_400(client: FlaskClient) -> None:
    _register_and_verify(client, "resetuser5")
    with patch("src.app.services.auth.send_password_reset_email") as mock_send:
        client.post(
            "/api/auth/forgot-password",
            json={"email": "resetuser5@example.com"},
        )
        captured_token: str = mock_send.call_args[0][1]

    with client.application.app_context():
        user = User.query.filter_by(username="resetuser5").one()
        user.password_reset_expires_at = datetime.utcnow() - timedelta(minutes=1)
        db.session.commit()

    response: TestResponse = client.post(
        "/api/auth/reset-password",
        json={"token": captured_token, "new_password": "NewPass@9999"},
    )
    assert response.status_code == 400
    assert "expired" in response.get_json()["message"].lower()


def test_reset_password_token_cannot_be_reused(client: FlaskClient) -> None:
    _register_and_verify(client, "resetuser6")
    with patch("src.app.services.auth.send_password_reset_email") as mock_send:
        client.post(
            "/api/auth/forgot-password",
            json={"email": "resetuser6@example.com"},
        )
        captured_token: str = mock_send.call_args[0][1]

    client.post(
        "/api/auth/reset-password",
        json={"token": captured_token, "new_password": "NewPass@9999"},
    )
    second_response: TestResponse = client.post(
        "/api/auth/reset-password",
        json={"token": captured_token, "new_password": "AnotherPass@1"},
    )
    assert second_response.status_code == 400


def test_reset_password_with_weak_password_returns_400(client: FlaskClient) -> None:
    _register_and_verify(client, "resetuser7")
    with patch("src.app.services.auth.send_password_reset_email") as mock_send:
        client.post(
            "/api/auth/forgot-password",
            json={"email": "resetuser7@example.com"},
        )
        captured_token: str = mock_send.call_args[0][1]

    response: TestResponse = client.post(
        "/api/auth/reset-password",
        json={"token": captured_token, "new_password": "weak"},
    )
    assert response.status_code == 400


def test_reset_password_missing_fields_returns_400(client: FlaskClient) -> None:
    response: TestResponse = client.post(
        "/api/auth/reset-password",
        json={"token": "sometoken"},
    )
    assert response.status_code == 400
    assert "new_password" in response.get_json()["message"].lower()


def test_new_password_works_for_login(client: FlaskClient) -> None:
    """After a successful reset, the user can log in with the new password."""

    _register_and_verify(client, "resetuser8")
    with patch("src.app.services.auth.send_password_reset_email") as mock_send:
        client.post(
            "/api/auth/forgot-password",
            json={"email": "resetuser8@example.com"},
        )
        captured_token: str = mock_send.call_args[0][1]

    client.post(
        "/api/auth/reset-password",
        json={"token": captured_token, "new_password": "NewPass@9999"},
    )

    with patch("src.app.services.auth.send_login_otp"):
        login_response: TestResponse = client.post(
            "/api/auth/login",
            json={"username": "resetuser8", "password": "NewPass@9999"},
        )
    assert login_response.status_code == 202
    assert login_response.get_json()["requires_otp"] is True
