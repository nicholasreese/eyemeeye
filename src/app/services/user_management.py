"""Services for user management operations."""

from __future__ import annotations

from typing import Any, Sequence

from ..extensions import db
from ..models import PhoneStatus, PhoneStatusHistory, Role, User
from .auth import AuthService


class UserManagementError(Exception):
    """Raised when user management operations fail."""


class UserNotFoundError(UserManagementError):
    """Raised when a requested user cannot be located."""


class UserManagementService:
    """Provides business logic for user administration and auditing."""

    def __init__(self, auth_service: AuthService | None = None) -> None:
        self._auth_service = auth_service or AuthService()

    def list_users(self) -> list[dict[str, Any]]:
        """Retrieves a serialized list of all users.

        Returns:
            list[dict[str, Any]]: List of user dictionaries sorted by username.
        """

        users: Sequence[User] = User.query.order_by(User.username.asc()).all()
        return [self._serialize_user(user) for user in users]

    def get_user_details(self, username: str) -> dict[str, Any]:
        """Fetches a user's profile and status history.

        Args:
            username (str): Username to retrieve.

        Returns:
            dict[str, Any]: User profile with status history.

        Raises:
            UserNotFoundError: If the user does not exist.
        """

        user = User.query.filter_by(username=username).one_or_none()
        if not user:
            raise UserNotFoundError("User not found.")
        statuses: Sequence[PhoneStatusHistory] = (
            PhoneStatusHistory.query.filter_by(user_id=user.id)
            .order_by(PhoneStatusHistory.noted_at.desc())
            .all()
        )
        return {
            "user": self._serialize_user(user),
            "status_history": [
                {
                    "status": record.status.value,
                    "noted_at": record.noted_at.isoformat(),
                }
                for record in statuses
            ],
        }

    def update_user_details(
        self,
        acting_user: User,
        username: str,
        updates: dict[str, Any],
    ) -> dict[str, Any]:
        """Updates mutable user fields as an administrative action.

        Args:
            acting_user (User): User performing the update.
            username (str): Username to update.
            updates (dict[str, Any]): Fields to update for the target user.

        Returns:
            dict[str, Any]: Updated user representation.

        Raises:
            AuthorizationError: If the acting user lacks admin privileges.
            UserNotFoundError: If the user does not exist.
            UserManagementError: If the payload contains invalid data.
        """

        self._auth_service.require_roles(acting_user, [Role.ADMIN])

        user = User.query.filter_by(username=username).one_or_none()
        if not user:
            raise UserNotFoundError("User not found.")

        email = updates.get("email")
        phone_number = updates.get("phone_number")
        imei = updates.get("imei")
        role_value = updates.get("role")

        if email is not None:
            if "@" not in email:
                raise UserManagementError("Invalid email address.")
            user.email = email

        if phone_number is not None:
            if not phone_number.isdigit() or len(phone_number) < 10:
                raise UserManagementError(
                    "Phone number must be numeric with 10+ digits."
                )
            user.phone_number = phone_number

        if imei is not None:
            if len(imei) not in {14, 15}:
                raise UserManagementError("IMEI must be 14 or 15 digits long.")
            user.imei = imei

        if role_value is not None:
            try:
                role = Role(role_value)
            except ValueError as exc:
                raise UserManagementError("Invalid role.") from exc
            user.role = role

        db.session.commit()
        return self._serialize_user(user)

    def _serialize_user(self, user: User) -> dict[str, Any]:
        """Serializes a user SQLAlchemy model.

        Args:
            user (User): User to serialize.

        Returns:
            dict[str, Any]: Serialized representation.
        """

        return {
            "username": user.username,
            "email": user.email,
            "phone_number": user.phone_number,
            "imei": user.imei,
            "role": user.role.value,
        }


class PhoneStatusQueryService:
    """Provides read-only access to phone status history."""

    def list_statuses(self, user: User) -> list[dict[str, str]]:
        """Returns the status history for a user.

        Args:
            user (User): User whose statuses are requested.

        Returns:
            list[dict[str, str]]: Ordered status history entries.
        """

        records: Sequence[PhoneStatusHistory] = (
            PhoneStatusHistory.query.filter_by(user_id=user.id)
            .order_by(PhoneStatusHistory.noted_at.desc())
            .all()
        )
        return [
            {
                "status": record.status.value,
                "noted_at": record.noted_at.isoformat(),
            }
            for record in records
        ]

    def list_allowed_statuses(self) -> list[str]:
        """Provides the allowed phone status values.

        Returns:
            list[str]: Enumerated allowed statuses.
        """

        return [status.value for status in PhoneStatus]
