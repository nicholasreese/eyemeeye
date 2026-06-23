"""Authentication-related endpoints."""

from __future__ import annotations

from typing import Any, Callable, TypeVar, cast

from flask import Blueprint, request
from flask_login import current_user, login_required, login_user, logout_user

from ..services.auth import AccountLockedError, AuthError, AuthService
from ..services.validation import (
    ForgotPasswordData,
    LoginData,
    OtpData,
    RegisterData,
    ResetPasswordData,
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
    """Registers a new application user and sends a verification email."""

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

    return {
        "message": (
            f"User {user.username} registered. "
            "Please check your email to verify your account before signing in."
        )
    }, 201


@auth_bp.post("/login")
def login() -> tuple[dict[str, object], int]:
    """Validates credentials and sends a one-time login code to the user's email.

    Returns HTTP 202 with ``requires_otp: true`` on success. The session is
    not created until the code is confirmed via ``POST /verify-otp``.
    """

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

    if not user.is_email_verified:
        return error_response(
            "Email address not verified. Please check your inbox for the verification link.",
            403,
        )

    auth_service.generate_and_send_login_otp(user)
    return {
        "message": "A verification code has been sent to your email.",
        "requires_otp": True,
    }, 202


@auth_bp.post("/verify-otp")
def verify_otp() -> tuple[dict[str, object], int]:
    """Verifies the email OTP and creates an authenticated session."""

    payload = request.get_json(silent=True)
    try:
        otp_data: OtpData = validation_service.parse_otp_payload(payload)
        user = auth_service.verify_login_otp(otp_data.username, otp_data.otp)
    except ValidationError as exc:
        return validation_error_response(str(exc))
    except AccountLockedError as exc:
        return error_response(str(exc), 429)
    except AuthError as exc:
        return error_response(str(exc), 401)

    login_user(user)
    return {"message": "Login successful."}, 200


@auth_bp.get("/verify-email")
def verify_email() -> tuple[dict[str, object], int]:
    """Verifies a user's email address using the token from the registration email."""

    token = request.args.get("token", "").strip()
    if not token:
        return error_response("Verification token is required.", 400)
    try:
        auth_service.verify_email_token(token)
    except AuthError as exc:
        return error_response(str(exc), 400)

    return {"message": "Email verified. You may now sign in."}, 200


@auth_bp.post("/forgot-password")
def forgot_password() -> tuple[dict[str, object], int]:
    """Sends a password reset email to the provided address if it is registered.

    Always returns HTTP 200 regardless of whether the email exists to avoid
    leaking account information.
    """

    payload = request.get_json(silent=True)
    try:
        data: ForgotPasswordData = validation_service.parse_forgot_password_payload(payload)
    except ValidationError as exc:
        return validation_error_response(str(exc))

    auth_service.request_password_reset(data.email)
    return {
        "message": "If that email is registered, a password reset link has been sent."
    }, 200


@auth_bp.post("/reset-password")
def reset_password_route() -> tuple[dict[str, object], int]:
    """Resets a user's password using a valid reset token."""

    payload = request.get_json(silent=True)
    try:
        data: ResetPasswordData = validation_service.parse_reset_password_payload(payload)
        auth_service.reset_password(data.token, data.new_password)
    except ValidationError as exc:
        return validation_error_response(str(exc))
    except AuthError as exc:
        return error_response(str(exc), 400)

    return {"message": "Password reset successful. You may now sign in."}, 200


@auth_bp.post("/logout")
@login_required_view
def logout() -> tuple[dict[str, object], int]:
    """Logs out the current session user."""

    username = getattr(current_user, "username", "unknown")
    logout_user()
    return {"message": f"User {username} logged out."}, 200
