"""Unit tests for model dataclasses and validation helpers."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.app.models import PhoneStatus, PhoneStatusRecord, Role, UserProfile


def test_user_profile_validates_username_length() -> None:
    """UserProfile should reject usernames shorter than three characters."""

    with pytest.raises(ValueError, match="Username must be at least 3"):
        UserProfile(
            username="ab",
            email="user@example.com",
            phone_number="1234567890",
            imei="12345678901234",
            role=Role.USER,
        )


def test_user_profile_validates_email_format() -> None:
    """UserProfile should reject email addresses without @ symbol."""

    with pytest.raises(ValueError, match="Email address must contain"):
        UserProfile(
            username="valid",
            email="invalid",
            phone_number="1234567890",
            imei="12345678901234",
            role=Role.USER,
        )


def test_phone_status_record_defaults_timestamp() -> None:
    """PhoneStatusRecord should set noted_at to a timezone-aware timestamp."""

    record = PhoneStatusRecord(username="user", status=PhoneStatus.ONLINE)

    assert record.noted_at.tzinfo is not None
    assert record.noted_at.tzinfo == timezone.utc


def test_phone_status_record_requires_username() -> None:
    """PhoneStatusRecord should reject empty usernames."""

    with pytest.raises(ValueError, match="username is required"):
        PhoneStatusRecord(
            username="",
            status=PhoneStatus.SOLD,
            noted_at=datetime.now(tz=timezone.utc),
        )
