"""Security utilities including password hashing and 2FA."""

from __future__ import annotations

import re
import secrets
from typing import Protocol

import pyotp
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


class HashingError(Exception):
    """Raised when password hashing or verification fails."""


class PasswordComplexityError(Exception):
    """Raised when a password does not meet complexity requirements."""


class PasswordHasherProtocol(Protocol):
    """Protocol describing the password hasher interface."""

    def hash(self, password: str) -> str:  # pragma: no cover - interface
        ...

    def verify(self, hash: str, password: str) -> bool:  # pragma: no cover - interface
        ...


class SecurityService:
    """Provides password hashing, complexity validation, and 2FA utilities."""

    _MIN_PASSWORD_LENGTH = 8
    _MAX_PASSWORD_LENGTH = 128
    _SPECIAL_CHARS = re.compile(r"[@$!%*?&]")
    _UPPERCASE = re.compile(r"[A-Z]")
    _LOWERCASE = re.compile(r"[a-z]")
    _DIGIT = re.compile(r"\d")

    def __init__(self, hasher: PasswordHasherProtocol | None = None) -> None:
        self._hasher = hasher or PasswordHasher()

    def validate_password_complexity(self, password: str) -> None:
        """Validates that a password meets complexity requirements.

        Password must be 8–128 characters and contain at least one each of:
        uppercase letter, lowercase letter, digit, and special character
        from the set ``@$!%*?&``. Any other characters are permitted.

        Args:
            password (str): Password to validate.

        Raises:
            PasswordComplexityError: If password does not meet requirements.
        """

        if len(password) < self._MIN_PASSWORD_LENGTH:
            raise PasswordComplexityError(
                "Password must be at least 8 characters long."
            )
        if len(password) > self._MAX_PASSWORD_LENGTH:
            raise PasswordComplexityError("Password must not exceed 128 characters.")
        if not self._UPPERCASE.search(password):
            raise PasswordComplexityError(
                "Password must contain at least one uppercase letter."
            )
        if not self._LOWERCASE.search(password):
            raise PasswordComplexityError(
                "Password must contain at least one lowercase letter."
            )
        if not self._DIGIT.search(password):
            raise PasswordComplexityError(
                "Password must contain at least one digit."
            )
        if not self._SPECIAL_CHARS.search(password):
            raise PasswordComplexityError(
                "Password must contain at least one special character (@$!%*?&)."
            )

    def hash_password(self, password: str) -> str:
        """Hashes the provided password using Argon2.

        Args:
            password (str): Password to hash. Must meet complexity requirements.

        Returns:
            str: Argon2 password hash.

        Raises:
            PasswordComplexityError: If password does not meet complexity requirements.
            HashingError: If password hashing fails.
        """

        self.validate_password_complexity(password)
        try:
            return self._hasher.hash(password)
        except Exception as exc:  # pragma: no cover - defensive
            raise HashingError("Password hashing failed.") from exc

    def verify_password(self, hash_value: str, password: str) -> bool:
        """Verifies the given password against the stored hash.

        Args:
            hash_value (str): Stored password hash.
            password (str): Password to verify.

        Returns:
            bool: True if password matches hash, False otherwise.

        Raises:
            HashingError: If password verification fails.
        """

        try:
            return self._hasher.verify(hash_value, password)
        except VerifyMismatchError:
            return False
        except Exception as exc:  # pragma: no cover - defensive
            raise HashingError("Password verification failed.") from exc

    def generate_two_factor_secret(self) -> str:
        """Generates a random secret for TOTP-based 2FA.

        Returns:
            str: Base32-encoded random secret for TOTP.
        """

        return pyotp.random_base32()

    def generate_email_otp(self) -> tuple[str, str]:
        """Generates a 6-digit email OTP and returns the plaintext and its hash.

        Returns:
            tuple[str, str]: (plaintext_otp, argon2_hash) pair. Store only
            the hash; pass the plaintext to the user via email.
        """

        otp = f"{secrets.randbelow(1_000_000):06d}"
        otp_hash = self._hasher.hash(otp)
        return otp, otp_hash
