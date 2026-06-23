"""Email sending utilities via Flask-Mail."""

from __future__ import annotations

import logging

from flask import request, url_for
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


def send_password_reset_email(email: str, token: str) -> None:
    """Sends a password reset email with a one-time link.

    Args:
        email (str): Recipient email address.
        token (str): Password reset token to include in the link.
    """

    try:
        logger.info("Sending password reset email to %s", email)
        base = request.host_url.rstrip("/")
        reset_url = f"{base}/?reset_token={token}"
        msg = Message(
            subject="Reset your EyeMeEye password",
            recipients=[email],
            body=(
                "You requested a password reset for your EyeMeEye account.\n\n"
                "Click the link below to set a new password:\n\n"
                f"  {reset_url}\n\n"
                "This link expires in 1 hour.\n\n"
                "If you did not request a password reset, you can ignore this email.\n"
            ),
        )
        mail.send(msg)
    except Exception:
        logger.exception("Failed to send password reset email to %s", email)


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
