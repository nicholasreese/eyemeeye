"""Integration tests for user status management endpoints."""

from __future__ import annotations

from typing import Any, Mapping

import pyotp
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from src.app.models import Role, User


def _register_user(
    client: FlaskClient,
    username: str,
    role: Role = Role.USER,
    overrides: Mapping[str, str] | None = None,
) -> User:
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
        return user


def _login_user(client: FlaskClient, username: str) -> None:
    with client.application.app_context():
        user = User.query.filter_by(username=username).one()
        totp = pyotp.TOTP(user.two_factor_secret)
        token = totp.now()
    response: TestResponse = client.post(
        "/api/auth/login",
        json={"username": username, "password": "Test@1234", "token": token},
    )
    assert response.status_code == 200


def test_user_can_fetch_profile(client: FlaskClient) -> None:
    """Users should retrieve their own profile."""

    _register_user(client, "member")
    _login_user(client, "member")

    response: TestResponse = client.get("/api/users/me")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["username"] == "member"


def test_user_can_update_status_and_history(client: FlaskClient) -> None:
    """Users should update status and view their history."""

    _register_user(client, "member")
    _login_user(client, "member")

    update_response: TestResponse = client.post(
        "/api/users/status", json={"status": "online"}
    )
    assert update_response.status_code == 200

    options_response: TestResponse = client.get("/api/users/status/options")
    assert options_response.status_code == 200
    options_payload: dict[str, Any] = options_response.get_json()
    assert "online" in options_payload["statuses"]

    history_response: TestResponse = client.get("/api/users/status/history")
    assert history_response.status_code == 200
    history_payload: dict[str, Any] = history_response.get_json()
    history = history_payload["status_history"]
    assert history
    assert history[0]["status"] == "online"


def test_invalid_status_returns_validation_error(client: FlaskClient) -> None:
    """Invalid status payloads should be rejected."""

    _register_user(client, "invalidstatus")
    _login_user(client, "invalidstatus")
    response: TestResponse = client.post(
        "/api/users/status", json={"status": "unknown"}
    )
    assert response.status_code == 400
    payload = response.get_json()
    assert "status" in payload["message"]
