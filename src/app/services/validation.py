"""Request payload validation utilities and data models."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping

from ..models import PhoneStatus, Role


class ValidationError(Exception):
    """Raised when incoming request payloads fail validation."""


@dataclass(frozen=True)
class RegisterData:
    """Validated payload for user registration requests."""

    username: str
    email: str
    phone_number: str
    imei: str
    password: str
    role: Role

    def __post_init__(self) -> None:
        """Performs field-level validation for registration data."""

        if len(self.username) < 3:
            raise ValidationError("username must be at least 3 characters long")
        if len(self.username) > 80:
            raise ValidationError("username must not exceed 80 characters")
        if not _is_valid_email(self.email):
            raise ValidationError("email must be a valid email address")
        if not self.phone_number.isdigit() or len(self.phone_number) < 10:
            raise ValidationError("phone_number must be numeric with 10+ digits")
        if len(self.imei) not in {14, 15} or not self.imei.isdigit():
            raise ValidationError("imei must contain 14 or 15 numeric digits")
        _validate_password_complexity(self.password)


@dataclass(frozen=True)
class LoginData:
    """Validated payload for login requests."""

    username: str
    password: str
    token: str | None

    def __post_init__(self) -> None:
        """Validates login-specific fields."""

        if len(self.username) < 3:
            raise ValidationError("username must be at least 3 characters long")
        if not self.password:
            raise ValidationError("password is required")
        if self.token is not None and not _is_valid_totp(self.token):
            raise ValidationError("token must be a 6-digit numeric string")


@dataclass(frozen=True)
class StatusUpdateData:
    """Validated payload for user status update requests."""

    status: PhoneStatus


@dataclass(frozen=True)
class RoleUpdateData:
    """Validated payload for role update requests."""

    role: Role


@dataclass(frozen=True)
class UserUpdateData:
    """Validated payload for administrative user updates."""

    email: str | None
    phone_number: str | None
    imei: str | None
    role: Role | None


class ValidationService:
    """Provides helpers for validating and coercing incoming payloads."""

    @staticmethod
    def ensure_json_payload(payload: Mapping[str, Any] | None) -> Mapping[str, Any]:
        """Ensures a JSON payload is present for the request."""

        if payload is None:
            raise ValidationError("Request body must be valid JSON")
        if not isinstance(payload, Mapping):
            raise ValidationError("Request body must be a JSON object")
        return payload

    @staticmethod
    def parse_register_payload(payload: Mapping[str, Any] | None) -> RegisterData:
        """Parses and validates registration payload content."""

        data = ValidationService.ensure_json_payload(payload)
        required_fields = {"username", "email", "phone_number", "imei", "password"}
        missing = required_fields - data.keys()
        if missing:
            field_list = ", ".join(sorted(missing))
            raise ValidationError(f"Missing required fields: {field_list}")
        role_value = data.get("role", Role.USER.value)
        try:
            role = Role(role_value)
        except ValueError as exc:  # pragma: no cover - defensive
            raise ValidationError("role must be one of admin, manager, user") from exc
        return RegisterData(
            username=str(data["username"]).strip(),
            email=str(data["email"]).strip(),
            phone_number=str(data["phone_number"]).strip(),
            imei=str(data["imei"]).strip(),
            password=str(data["password"]),
            role=role,
        )

    @staticmethod
    def parse_login_payload(payload: Mapping[str, Any] | None) -> LoginData:
        """Parses and validates login payload content."""

        data = ValidationService.ensure_json_payload(payload)
        required_fields = {"username", "password"}
        missing = required_fields - data.keys()
        if missing:
            field_list = ", ".join(sorted(missing))
            raise ValidationError(f"Missing required fields: {field_list}")
        token = data.get("token")
        return LoginData(
            username=str(data["username"]).strip(),
            password=str(data["password"]),
            token=str(token).strip() if token is not None else None,
        )

    @staticmethod
    def parse_status_payload(payload: Mapping[str, Any] | None) -> StatusUpdateData:
        """Parses and validates phone status update payloads."""

        data = ValidationService.ensure_json_payload(payload)
        if "status" not in data:
            raise ValidationError("status is required")
        try:
            status = PhoneStatus(str(data["status"]).strip())
        except ValueError as exc:
            raise ValidationError(
                "status must be one of online, sold, stolen, disposed"
            ) from exc
        return StatusUpdateData(status=status)

    @staticmethod
    def parse_role_payload(payload: Mapping[str, Any] | None) -> RoleUpdateData:
        """Parses and validates administrative role update payloads."""

        data = ValidationService.ensure_json_payload(payload)
        if "role" not in data:
            raise ValidationError("role is required")
        try:
            role = Role(str(data["role"]).strip())
        except ValueError as exc:
            raise ValidationError("role must be one of admin, manager, user") from exc
        return RoleUpdateData(role=role)

    @staticmethod
    def parse_user_update_payload(payload: Mapping[str, Any] | None) -> UserUpdateData:
        """Parses and validates user metadata update payloads."""

        data = ValidationService.ensure_json_payload(payload)
        if not data:
            raise ValidationError("At least one updatable field must be provided")
        allowed = {"email", "phone_number", "imei", "role"}
        unknown = set(data.keys()) - allowed
        if unknown:
            field_list = ", ".join(sorted(unknown))
            raise ValidationError(f"Unsupported fields provided: {field_list}")
        email = _sanitize_optional_string(data.get("email"))
        phone_number = _sanitize_optional_string(data.get("phone_number"))
        imei = _sanitize_optional_string(data.get("imei"))
        role_value = data.get("role")
        role = None
        if role_value is not None:
            try:
                role = Role(str(role_value).strip())
            except ValueError as exc:
                raise ValidationError(
                    "role must be one of admin, manager, user"
                ) from exc
        if email is not None and not _is_valid_email(email):
            raise ValidationError("email must be a valid email address")
        if phone_number is not None and (
            not phone_number.isdigit() or len(phone_number) < 10
        ):
            raise ValidationError("phone_number must be numeric with 10+ digits")
        if imei is not None and (len(imei) not in {14, 15} or not imei.isdigit()):
            raise ValidationError("imei must contain 14 or 15 numeric digits")
        return UserUpdateData(
            email=email,
            phone_number=phone_number,
            imei=imei,
            role=role,
        )


def _is_valid_email(value: str) -> bool:
    """Validates that the provided string looks like an email address."""

    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return bool(re.match(pattern, value))


def _is_valid_totp(value: str) -> bool:
    """Validates that the provided TOTP value is a 6-digit string."""

    return value.isdigit() and len(value) == 6


def _sanitize_optional_string(value: Any) -> str | None:
    """Converts optional payload values into sanitized strings."""

    if value is None:
        return None
    string_value = str(value).strip()
    return string_value or None


def _validate_password_complexity(password: str) -> None:
    """Validates password meets complexity requirements.

    Password must contain:
    - At least 8 characters (max 128)
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character (@$!%*?&)

    Args:
        password (str): Password to validate.

    Raises:
        ValidationError: If password does not meet requirements.
    """

    if len(password) < 8:
        raise ValidationError("password must be at least 8 characters long")
    if len(password) > 128:
        raise ValidationError("password must not exceed 128 characters")
    if not re.search(r"[A-Z]", password):
        raise ValidationError("password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", password):
        raise ValidationError("password must contain at least one lowercase letter")
    if not re.search(r"\d", password):
        raise ValidationError("password must contain at least one digit")
    if not re.search(r"[@$!%*?&]", password):
        raise ValidationError(
            "password must contain at least one special character (@$!%*?&)"
        )
