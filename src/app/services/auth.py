"""Authentication and authorization service layer."""

from __future__ import annotations

from typing import Iterable, Optional, Sequence, cast

import pyotp
from flask_login import UserMixin
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import PhoneStatus, Role, User
from ..utils.email import send_verification_email
from .auditing import SecurityAuditService
from .security import PasswordComplexityError, SecurityService


class AuthError(Exception):
    """Raised when authentication operations fail."""


class AuthorizationError(Exception):
    """Raised when authorization checks fail."""


class AccountLockedError(AuthError):
    """Raised when a user account is locked due to security policy."""


class AuthService:
    """Handles registration, login, and authorization logic with security auditing.

    This service enforces account lockout policies after repeated failed login
    attempts and logs all authentication-related security events.
    """

    _MAX_FAILED_ATTEMPTS = 5

    def __init__(
        self,
        security_service: SecurityService | None = None,
        audit_service: SecurityAuditService | None = None,
    ) -> None:
        self._security = security_service or SecurityService()
        self._audit = audit_service or SecurityAuditService()

    def register_user(
        self,
        username: str,
        email: str,
        phone_number: str,
        imei: str,
        password: str,
        role: Role = Role.USER,
    ) -> User:
        """Registers a new user with validated profile data.

        Args:
            username (str): Desired username.
            email (str): User email address.
            phone_number (str): User phone number.
            imei (str): Device IMEI.
            password (str): User password (must meet complexity requirements).
            role (Role): Initial user role. Defaults to Role.USER.

        Returns:
            User: Newly registered user object.

        Raises:
            AuthError: If registration fails (duplicate username/email).
            PasswordComplexityError: If password does not meet requirements.
        """

        try:
            password_hash = self._security.hash_password(password)
        except PasswordComplexityError as exc:
            raise AuthError(str(exc)) from exc

        two_factor_secret = self._security.generate_two_factor_secret()
        verification_token = self._security.generate_two_factor_secret()
        user = User()
        user.username = username
        user.email = email
        user.phone_number = phone_number
        user.imei = imei
        user.password_hash = password_hash
        user.role = role
        user.two_factor_secret = two_factor_secret
        user.email_verification_token = verification_token

        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError as exc:  # pragma: no cover - DB constraint
            db.session.rollback()
            raise AuthError("Username or email already exists.") from exc

        send_verification_email(email, verification_token)

        return user

    def verify_totp(self, user: User, token: str) -> bool:
        """Verifies the provided TOTP token using the stored secret.

        Args:
            user (User): User object with 2FA secret.
            token (str): TOTP token to verify.

        Returns:
            bool: True if token is valid, False otherwise.
        """

        if not user.two_factor_secret:
            return False
        totp = pyotp.TOTP(user.two_factor_secret)
        return totp.verify(token, valid_window=1)

    def _is_account_locked(self, username: str) -> bool:
        """Checks if an account is locked due to failed login attempts.

        Args:
            username (str): Username to check.

        Returns:
            bool: True if account is locked, False otherwise.
        """

        failed_count = self._audit.get_failed_login_count(username)
        return failed_count >= self._MAX_FAILED_ATTEMPTS

    def authenticate(self, username: str, password: str) -> User:
        """Authenticates a user by verifying their credentials.

        Enforces account lockout after repeated failed attempts and logs
        all authentication events for audit trail.

        Args:
            username (str): Username to authenticate.
            password (str): Password to verify.

        Returns:
            User: Authenticated user object.

        Raises:
            AccountLockedError: If account is locked.
            AuthError: If authentication fails.
        """

        if self._is_account_locked(username):
            self._audit.log_unauthorized_access_attempt(
                username, "login", "Account locked due to failed login attempts"
            )
            raise AccountLockedError("Account is locked. Please contact support.")

        user = User.query.filter_by(username=username).one_or_none()
        if not user:
            self._audit.log_failed_login(username, "User not found")
            raise AuthError("Invalid username or password.")

        if not self._security.verify_password(user.password_hash, password):
            self._audit.log_failed_login(username, "Invalid password")
            if self._is_account_locked(username):
                self._audit.log_account_locked(username)
                raise AccountLockedError("Account is locked. Please contact support.")
            raise AuthError("Invalid username or password.")

        self._audit.clear_failed_login_attempts(username)
        self._audit.log_successful_login(username)

        return cast(User, user)

    @staticmethod
    def load_user_by_id(user_id: str) -> User | None:
        """Loads a user for Flask-Login by identifier.

        Args:
            user_id (str): User ID to load.

        Returns:
            User | None: User object if found, None otherwise.
        """

        if not user_id.isdigit():
            return None
        return cast(Optional[User], User.query.get(int(user_id)))

    def require_roles(self, user: UserMixin, allowed_roles: Iterable[Role]) -> None:
        """Ensures the current user possesses one of the allowed roles.

        Args:
            user (UserMixin): User to check.
            allowed_roles (Iterable[Role]): Roles that are permitted.

        Raises:
            AuthorizationError: If user does not have required role.
        """

        allowed: Sequence[Role] = tuple(allowed_roles)
        user_role = cast(Optional[Role], getattr(user, "role", None))
        if user_role is None or user_role not in allowed:
            username = cast(Optional[str], getattr(user, "username", "unknown"))
            self._audit.log_unauthorized_access_attempt(
                username, "restricted endpoint", "Insufficient permissions"
            )
            raise AuthorizationError("You do not have permission for this action.")


class PhoneStatusService:
    """Manages phone status transitions and audit logging."""

    def log_status(self, user: User, status: PhoneStatus) -> None:
        """Appends a phone status history entry for the given user.

        Args:
            user (User): User for whom the status is being logged.
            status (PhoneStatus): Status value to persist.
        """

        from ..models import PhoneStatusHistory

        history_entry = PhoneStatusHistory()
        history_entry.user_id = user.id
        history_entry.status = status
        db.session.add(history_entry)
        db.session.commit()
