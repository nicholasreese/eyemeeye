"""Email sending utilities (placeholder for real integration)."""

from __future__ import annotations

import logging

logger = logging.getLogger()


def send_verification_email(email: str, token: str) -> None:
    """Logs that a verification email would be sent."""

    logger.info("Sending verification email", extra={"email": email, "token": token})
