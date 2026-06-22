"""Email sending utilities via Flask-Mail."""

from __future__ import annotations

import logging

from flask import url_for
from flask_mail import Message

from ..extensions import mail

logger = logging.getLogger(__name__)


def send_verification_email(email: str, token: str) -> None:
    """Sends an account verification email with a confirmation link.

    Args:
        email (str): Recipient email address.
        token (str): Email verification token to include in the link.
    """

    try:
        logger.info("Sending verification email to %s", email)
        verify_url = url_for("auth.verify_email", token=token, _external=True)
        msg = Message(
            subject="Verify your EyeMeEye email address",
            recipients=[email],
            body=(
                "Welcome to EyeMeEye!\n\n"
                "Please verify your email address by clicking the link below:\n\n"
                f"  {verify_url}\n\n"
                "If you did not create this account you can ignore this email.\n"
            ),
        )
        mail.send(msg)
    except Exception:
        logger.exception("Failed to send verification email to %s", email)


def send_login_otp(email: str, otp: str) -> None:
    """Sends a one-time login verification code to the user's email.

    Args:
        email (str): Recipient email address.
        otp (str): 6-digit OTP code to include in the message.
    """

    try:
        msg = Message(
            subject="Your EyeMeEye login code",
            recipients=[email],
            body=(
                "Your login verification code is:\n\n"
                f"    {otp}\n\n"
                "This code expires in 10 minutes. Do not share it with anyone.\n\n"
                "If you did not attempt to log in, please contact support.\n"
            ),
        )
        mail.send(msg)
    except Exception:
        logger.exception("Failed to send login OTP to %s", email)
