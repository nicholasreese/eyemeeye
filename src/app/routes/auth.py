"""Authentication-related endpoints."""

from __future__ import annotations

from typing import Any, Callable, TypeVar, cast

from flask import Blueprint, request
from flask_login import current_user, login_required, login_user, logout_user

from ..services.auth import AccountLockedError, AuthError, AuthService
from ..services.validation import (
    LoginData,
    RegisterData,
    ValidationError,
    ValidationService,
)
from .responses import error_response, validation_error_response

ViewFunc = TypeVar("ViewFunc", bound=Callable[..., Any])
login_required_view = cast(Callable[[ViewFunc], ViewFunc], login_required)

auth_bp = Blueprint("auth", __name__)
auth_service = AuthService()
validation_service = ValidationService()


@auth_bp.post("/register")
def register() -> tuple[dict[str, object], int]:
    """Registers a new application user."""

    payload = request.get_json(silent=True)
    try:
        register_data: RegisterData = validation_service.parse_register_payload(payload)
        user = auth_service.register_user(
            username=register_data.username,
            email=register_data.email,
            phone_number=register_data.phone_number,
            imei=register_data.imei,
            password=register_data.password,
            role=register_data.role,
        )
    except ValidationError as exc:
        return validation_error_response(str(exc))
    except AuthError as exc:
        return error_response(str(exc), 400)

    return {"message": f"User {user.username} registered."}, 201


@auth_bp.post("/login")
def login() -> tuple[dict[str, object], int]:
    """Authenticates the user and initiates a session."""

    payload = request.get_json(silent=True)
    try:
        login_data: LoginData = validation_service.parse_login_payload(payload)
        user = auth_service.authenticate(login_data.username, login_data.password)
    except ValidationError as exc:
        return validation_error_response(str(exc))
    except AccountLockedError as exc:
        return error_response(str(exc), 429)
    except AuthError as exc:
        return error_response(str(exc), 401)

    if login_data.token and not auth_service.verify_totp(user, login_data.token):
        return error_response("Invalid two-factor token.", 401)

    login_user(user)
    return {"message": "Login successful."}, 200


@auth_bp.post("/logout")
@login_required_view
def logout() -> tuple[dict[str, object], int]:
    """Logs out the current session user."""

    username = getattr(current_user, "username", "unknown")
    logout_user()
    return {"message": f"User {username} logged out."}, 200
