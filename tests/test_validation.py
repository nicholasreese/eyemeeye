"""Unit tests for validation utilities."""

from __future__ import annotations

import pytest

from src.app.models import Role
from src.app.services.validation import (
    LoginData,
    RegisterData,
    UserUpdateData,
    ValidationError,
    ValidationService,
    _is_valid_email,
    _is_valid_totp,
    _sanitize_optional_string,
    _validate_password_complexity,
)


def test_is_valid_email_accepts_valid_address() -> None:
    """_is_valid_email should return True for valid emails."""

    assert _is_valid_email("user@example.com")


def test_is_valid_email_rejects_invalid_address() -> None:
    """_is_valid_email should return False for invalid emails."""

    assert not _is_valid_email("invalid-email")


def test_is_valid_totp_requires_six_digits() -> None:
    """_is_valid_totp should only accept six digit values."""

    assert _is_valid_totp("123456")
    assert not _is_valid_totp("12345")
    assert not _is_valid_totp("abcdef")


def test_sanitize_optional_string_handles_empty_values() -> None:
    """_sanitize_optional_string should normalize empty values to None."""

    assert _sanitize_optional_string(None) is None
    assert _sanitize_optional_string("   ") is None
    assert _sanitize_optional_string(" value ") == "value"


def test_validate_password_complexity_rejects_short_password() -> None:
    """_validate_password_complexity should reject short passwords."""

    with pytest.raises(ValidationError, match="at least 8"):
        _validate_password_complexity("Aa1@")


def test_register_data_validation_accepts_valid_payload() -> None:
    """RegisterData should accept valid registration payloads."""

    data = RegisterData(
        username="validuser",
        email="valid@example.com",
        phone_number="1234567890",
        imei="12345678901234",
        password="ValidPass@123",
        role=Role.USER,
    )

    assert data.username == "validuser"


def test_login_data_validation_rejects_missing_password() -> None:
    """LoginData should reject blank passwords."""

    with pytest.raises(ValidationError, match="password is required"):
        LoginData(username="user", password="")


def test_user_update_payload_rejects_unknown_fields() -> None:
    """parse_user_update_payload should reject unsupported fields."""

    with pytest.raises(ValidationError, match="Unsupported fields"):
        ValidationService.parse_user_update_payload({"unknown": "value"})


def test_user_update_payload_parses_valid_fields() -> None:
    """parse_user_update_payload should allow valid update fields."""

    data = ValidationService.parse_user_update_payload(
        {"email": "new@example.com", "role": "manager"}
    )

    assert isinstance(data, UserUpdateData)
    assert data.email == "new@example.com"
    assert data.role == Role.MANAGER
