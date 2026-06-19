"""Unit tests for email utilities."""

from __future__ import annotations

import logging

import pytest

from src.app.utils.email import send_verification_email


def test_send_verification_email_logs_message(caplog: pytest.LogCaptureFixture) -> None:
    """send_verification_email should log the email payload."""

    with caplog.at_level(logging.INFO):
        send_verification_email("user@example.com", "token123")

    assert "Sending verification email" in caplog.text
