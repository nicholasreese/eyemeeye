"""Security utilities including password hashing and 2FA."""

from __future__ import annotations

import re
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
    _PASSWORD_PATTERN = re.compile(
        r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[a-zA-Z\d@$!%*?&]{8,128}$"
    )

    def __init__(self, hasher: PasswordHasherProtocol | None = None) -> None:
        self._hasher = hasher or PasswordHasher()

    def validate_password_complexity(self, password: str) -> None:
        """Validates that a password meets complexity requirements.

        Password must contain:
        - At least 8 characters (max 128)
        - At least one lowercase letter
        - At least one uppercase letter
        - At least one digit
        - At least one special character (@$!%*?&)

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
        if not self._PASSWORD_PATTERN.match(password):
            raise PasswordComplexityError(
                "Password must contain uppercase, lowercase, digit, and special "
                "character (@$!%*?&)."
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
        except VerifyMismatchError:  # pragma: no cover - deterministic
            return False
        except Exception as exc:  # pragma: no cover - defensive
            raise HashingError("Password verification failed.") from exc

    def generate_two_factor_secret(self) -> str:
        """Generates a random secret for TOTP-based 2FA.

        Returns:
            str: Base32-encoded random secret for TOTP.
        """

        return pyotp.random_base32()
