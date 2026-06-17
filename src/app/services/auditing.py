"""Security audit logging service for tracking security events."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from ..extensions import db
from ..models import AuditLog


class AuditingError(Exception):
    """Raised when audit logging operations fail."""


class SecurityAuditService:
    """Logs security-related events for audit trails and monitoring.

    This service provides centralized tracking of security events including
    failed login attempts, role changes, and administrative actions.
    """

    _logger = logging.getLogger(__name__)

    @staticmethod
    def log_failed_login(username: str, reason: str = "Invalid credentials") -> None:
        """Logs a failed login attempt.

        Args:
            username (str): Username that failed to authenticate.
            reason (str): Reason for the failure. Defaults to "Invalid credentials".

        Raises:
            AuditingError: If audit logging fails.
        """

        try:
            audit = AuditLog()
            audit.event_type = "failed_login"
            audit.username = username
            audit.message = f"Failed login attempt: {reason}"
            audit.created_at = datetime.now(tz=timezone.utc)
            db.session.add(audit)
            db.session.commit()
            SecurityAuditService._logger.warning(
                f"Failed login for user: {username}, reason: {reason}"
            )
        except Exception as exc:  # pragma: no cover - defensive
            raise AuditingError("Failed to log security event.") from exc

    @staticmethod
    def log_successful_login(username: str) -> None:
        """Logs a successful login event.

        Args:
            username (str): Username that successfully authenticated.

        Raises:
            AuditingError: If audit logging fails.
        """

        try:
            audit = AuditLog()
            audit.event_type = "successful_login"
            audit.username = username
            audit.message = "User successfully logged in"
            audit.created_at = datetime.now(tz=timezone.utc)
            db.session.add(audit)
            db.session.commit()
            SecurityAuditService._logger.info(f"Successful login for user: {username}")
        except Exception as exc:  # pragma: no cover - defensive
            raise AuditingError("Failed to log security event.") from exc

    @staticmethod
    def log_account_locked(username: str) -> None:
        """Logs when an account is locked due to failed login attempts.

        Args:
            username (str): Username whose account was locked.

        Raises:
            AuditingError: If audit logging fails.
        """

        try:
            audit = AuditLog()
            audit.event_type = "account_locked"
            audit.username = username
            audit.message = "Account locked due to multiple failed login attempts"
            audit.created_at = datetime.now(tz=timezone.utc)
            db.session.add(audit)
            db.session.commit()
            SecurityAuditService._logger.error(
                f"Account locked: {username} due to failed attempts"
            )
        except Exception as exc:  # pragma: no cover - defensive
            raise AuditingError("Failed to log security event.") from exc

    @staticmethod
    def log_role_change(
        acting_user: str, target_user: str, new_role: str, old_role: str
    ) -> None:
        """Logs when a user's role is modified by an administrator.

        Args:
            acting_user (str): Username performing the role change.
            target_user (str): Username whose role was changed.
            new_role (str): New role value.
            old_role (str): Previous role value.

        Raises:
            AuditingError: If audit logging fails.
        """

        try:
            audit = AuditLog()
            audit.event_type = "role_change"
            audit.username = acting_user
            audit.message = (
                f"Role changed for user {target_user} from {old_role} to {new_role}"
            )
            audit.created_at = datetime.now(tz=timezone.utc)
            db.session.add(audit)
            db.session.commit()
            SecurityAuditService._logger.info(
                f"Role change: {target_user} from {old_role} to {new_role} "
                f"by {acting_user}"
            )
        except Exception as exc:  # pragma: no cover - defensive
            raise AuditingError("Failed to log security event.") from exc

    @staticmethod
    def log_unauthorized_access_attempt(
        username: Optional[str], resource: str, reason: str
    ) -> None:
        """Logs unauthorized access attempts.

        Args:
            username (Optional[str]): Username attempting access (may be None).
            resource (str): Resource being accessed.
            reason (str): Reason access was denied.

        Raises:
            AuditingError: If audit logging fails.
        """

        try:
            audit = AuditLog()
            audit.event_type = "unauthorized_access"
            audit.username = username
            audit.message = f"Unauthorized access to {resource}: {reason}"
            audit.created_at = datetime.now(tz=timezone.utc)
            db.session.add(audit)
            db.session.commit()
            SecurityAuditService._logger.warning(
                f"Unauthorized access attempt by {username} to {resource}: {reason}"
            )
        except Exception as exc:  # pragma: no cover - defensive
            raise AuditingError("Failed to log security event.") from exc

    @staticmethod
    def get_failed_login_count(username: str) -> int:
        """Retrieves the count of recent failed login attempts for a user.

        Args:
            username (str): Username to check.

        Returns:
            int: Number of failed login attempts in the tracking window.
        """

        count: int = AuditLog.query.filter_by(
            event_type="failed_login", username=username
        ).count()
        return count

    @staticmethod
    def clear_failed_login_attempts(username: str) -> None:
        """Clears failed login tracking for a user after successful login.

        Args:
            username (str): Username whose failed login tracking should be cleared.

        Raises:
            AuditingError: If clearing fails.
        """

        try:
            AuditLog.query.filter_by(
                event_type="failed_login", username=username
            ).delete()
            db.session.commit()
        except Exception as exc:  # pragma: no cover - defensive
            raise AuditingError("Failed to clear login attempts.") from exc
