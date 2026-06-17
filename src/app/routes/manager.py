"""Manager and admin-facing endpoints."""

from __future__ import annotations

from typing import Any, Callable, TypeVar, cast

from flask import Blueprint, request
from flask_login import current_user, login_required

from ..models import Role, User
from ..services.auditing import SecurityAuditService
from ..services.auth import AuthorizationError, AuthService
from ..services.user_management import (
    PhoneStatusQueryService,
    UserManagementError,
    UserManagementService,
    UserNotFoundError,
)
from ..services.validation import (
    RoleUpdateData,
    UserUpdateData,
    ValidationError,
    ValidationService,
)
from .responses import error_response, validation_error_response

ViewFunc = TypeVar("ViewFunc", bound=Callable[..., Any])
login_required_view = cast(Callable[[ViewFunc], ViewFunc], login_required)

manager_bp = Blueprint("manager", __name__)
auth_service = AuthService()
audit_service = SecurityAuditService()
user_management_service = UserManagementService(auth_service=auth_service)
status_query_service = PhoneStatusQueryService()
validation_service = ValidationService()


def _ensure_manager() -> None:
    """Ensures the current user has manager or admin privileges.

    Raises:
        AuthorizationError: If the current user lacks manager or admin access.
    """

    auth_service.require_roles(cast(User, current_user), [Role.MANAGER, Role.ADMIN])


@manager_bp.get("/users")
@login_required_view
def list_users() -> tuple[dict[str, object], int]:
    """Lists user profiles for manager viewing.

    Returns:
        tuple[dict[str, object], int]: Serialized users payload and status code.
    """

    try:
        _ensure_manager()
    except AuthorizationError as exc:
        return error_response(str(exc), 403)

    users = user_management_service.list_users()
    return {"users": users}, 200


@manager_bp.get("/users/<string:username>")
@login_required_view
def get_user(username: str) -> tuple[dict[str, object], int]:
    """Returns the profile and history for a specific user.

    Args:
        username (str): Username to retrieve.

    Returns:
        tuple[dict[str, object], int]: User detail payload and status code.
    """

    try:
        _ensure_manager()
    except AuthorizationError as exc:
        return error_response(str(exc), 403)

    try:
        user_details = user_management_service.get_user_details(username)
    except UserNotFoundError as exc:
        return error_response(str(exc), 404)
    except UserManagementError as exc:
        return error_response(str(exc), 400)

    return user_details, 200


@manager_bp.patch("/users/<string:username>/role")
@login_required_view
def update_user_role(username: str) -> tuple[dict[str, object], int]:
    """Allows admins to promote or demote user roles.

    Args:
        username (str): Username whose role is being modified.

    Returns:
        tuple[dict[str, object], int]: Response message and status code.
    """

    try:
        auth_service.require_roles(cast(User, current_user), [Role.ADMIN])
    except AuthorizationError as exc:
        return error_response(str(exc), 403)

    payload = request.get_json(silent=True)
    try:
        role_data: RoleUpdateData = validation_service.parse_role_payload(payload)
    except ValidationError as exc:
        return validation_error_response(str(exc))

    user = User.query.filter_by(username=username).one_or_none()
    if not user:
        return error_response("User not found.", 404)

    old_role = user.role.value
    user.role = role_data.role
    auth_service.require_roles(user, [Role.USER, Role.MANAGER, Role.ADMIN])
    auth_service.require_roles(cast(User, current_user), [Role.ADMIN])
    from ..extensions import db

    db.session.commit()
    acting_user = cast(User, current_user).username
    audit_service.log_role_change(acting_user, username, role_data.role.value, old_role)
    return {"message": f"User {username} role updated to {role_data.role.value}."}, 200


@manager_bp.patch("/users/<string:username>")
@login_required_view
def update_user(username: str) -> tuple[dict[str, object], int]:
    """Updates user details as an admin.

    Args:
        username (str): Username to update.

    Returns:
        tuple[dict[str, object], int]: Updated user payload and status code.
    """

    try:
        payload = request.get_json(silent=True)
        update_data: UserUpdateData = validation_service.parse_user_update_payload(
            payload
        )
        updates = {
            key: value
            for key, value in {
                "email": update_data.email,
                "phone_number": update_data.phone_number,
                "imei": update_data.imei,
                "role": update_data.role.value if update_data.role else None,
            }.items()
            if value is not None
        }
        updated_user = user_management_service.update_user_details(
            acting_user=cast(User, current_user),
            username=username,
            updates=updates,
        )
    except ValidationError as exc:
        return validation_error_response(str(exc))
    except AuthorizationError as exc:
        return error_response(str(exc), 403)
    except UserNotFoundError as exc:
        return error_response(str(exc), 404)
    except UserManagementError as exc:
        return error_response(str(exc), 400)

    return {"user": updated_user}, 200


@manager_bp.get("/users/<string:username>/statuses")
@login_required_view
def list_user_statuses(username: str) -> tuple[dict[str, object], int]:
    """Provides status history for a user.

    Args:
        username (str): Username whose statuses are requested.

    Returns:
        tuple[dict[str, object], int]: Status history payload and status code.
    """

    try:
        _ensure_manager()
    except AuthorizationError as exc:
        return error_response(str(exc), 403)

    user = User.query.filter_by(username=username).one_or_none()
    if not user:
        return error_response("User not found.", 404)

    history = status_query_service.list_statuses(user)
    return {"username": username, "status_history": history}, 200
