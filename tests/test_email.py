"""Unit tests for email utilities."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from flask import Flask

from src.app.utils.email import send_verification_email


def test_send_verification_email_calls_mail_send(app: Flask) -> None:
    """send_verification_email should call mail.send with the recipient address."""

    with app.test_request_context():
        with patch("src.app.utils.email.mail") as mock_mail:
            send_verification_email("user@example.com", "token123")

    mock_mail.send.assert_called_once()
    message = mock_mail.send.call_args[0][0]
    assert "user@example.com" in message.recipients
    assert "Verify" in message.subject
