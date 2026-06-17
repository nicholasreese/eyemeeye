"""End-to-end tests for authentication and role-protected flows."""

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


def test_login_invalid_totp_returns_error(client: FlaskClient) -> None:
    _register_user(client, "totpuser")
    response: TestResponse = client.post(
        "/api/auth/login",
        json={
            "username": "totpuser",
            "password": "Test@1234",
            "token": "1234",
        },
    )
    assert response.status_code == 400
    payload = response.get_json()
    assert "token" in payload["message"]


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
