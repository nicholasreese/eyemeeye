"""Integration tests for manager and admin user management endpoints."""

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


def test_manager_can_view_users(client: FlaskClient) -> None:
    """Managers should be able to list all users."""

    _register_user(client, "manager", role=Role.MANAGER)
    _register_user(client, "member")
    _login_user(client, "manager")

    response: TestResponse = client.get("/api/manager/users")
    assert response.status_code == 200
    payload: dict[str, Any] = response.get_json()
    usernames = {user["username"] for user in payload["users"]}
    assert {"manager", "member"}.issubset(usernames)


def test_manager_can_view_user_details(client: FlaskClient) -> None:
    """Managers should retrieve details and status history for a user."""

    _register_user(client, "manager", role=Role.MANAGER)
    _register_user(client, "member")
    _login_user(client, "manager")

    response: TestResponse = client.get("/api/manager/users/member")
    assert response.status_code == 200
    payload: dict[str, Any] = response.get_json()
    assert payload["user"]["username"] == "member"
    assert "status_history" in payload


def test_admin_can_update_user_details(client: FlaskClient) -> None:
    """Admins should update user metadata and role."""

    _register_user(client, "admin", role=Role.ADMIN)
    _register_user(client, "member")
    _login_user(client, "admin")

    response: TestResponse = client.patch(
        "/api/manager/users/member",
        json={
            "email": "member_updated@example.com",
            "phone_number": "0987654321",
            "imei": "123456789012345",
            "role": Role.MANAGER.value,
        },
    )
    assert response.status_code == 200
    payload: dict[str, Any] = response.get_json()
    assert payload["user"]["email"] == "member_updated@example.com"
    assert payload["user"]["role"] == Role.MANAGER.value


def test_manager_cannot_update_user_details(client: FlaskClient) -> None:
    """Managers should be prevented from performing admin-only updates."""

    _register_user(client, "manager", role=Role.MANAGER)
    _register_user(client, "member")
    _login_user(client, "manager")

    response: TestResponse = client.patch(
        "/api/manager/users/member", json={"email": "x@example.com"}
    )
    assert response.status_code == 403


def test_manager_can_view_status_history(client: FlaskClient) -> None:
    """Managers should retrieve a user's status history."""

    _register_user(client, "manager", role=Role.MANAGER)
    _register_user(client, "member")
    _login_user(client, "member")
    client.post("/api/users/status", json={"status": "online"})

    _login_user(client, "manager")
    response: TestResponse = client.get("/api/manager/users/member/statuses")
    assert response.status_code == 200
    payload: dict[str, Any] = response.get_json()
    assert payload["username"] == "member"
    assert payload["status_history"]
