"""User-facing endpoints for managing phone statuses."""

from __future__ import annotations

from typing import Any, Callable, TypeVar, cast

from flask import Blueprint, request
from flask_login import current_user, login_required

from ..models import User
from ..services.auth import PhoneStatusService
from ..services.user_management import PhoneStatusQueryService
from ..services.validation import (
    StatusUpdateData,
    ValidationError,
    ValidationService,
)
from .responses import validation_error_response

ViewFunc = TypeVar("ViewFunc", bound=Callable[..., Any])
login_required_view = cast(Callable[[ViewFunc], ViewFunc], login_required)

user_bp = Blueprint("user", __name__)
status_service = PhoneStatusService()
status_query_service = PhoneStatusQueryService()
validation_service = ValidationService()


@user_bp.get("/me")
@login_required_view
def get_profile() -> tuple[dict[str, object], int]:
    """Returns the authenticated user's profile."""

    user = cast(User, current_user)
    return (
        {
            "username": user.username,
            "email": user.email,
            "phone_number": user.phone_number,
            "imei": user.imei,
            "role": user.role.value,
        },
        200,
    )


@user_bp.post("/status")
@login_required_view
def update_status() -> tuple[dict[str, object], int]:
    """Updates the user's phone status."""

    payload = request.get_json(silent=True)
    try:
        status_data: StatusUpdateData = validation_service.parse_status_payload(payload)
    except ValidationError as exc:
        return validation_error_response(str(exc))

    status_service.log_status(cast(User, current_user), status_data.status)
    return {"message": f"Status updated to {status_data.status.value}."}, 200


@user_bp.get("/status/options")
@login_required_view
def get_status_options() -> tuple[dict[str, object], int]:
    """Returns the allowable phone status values for selection.

    Returns:
        tuple[dict[str, object], int]: Allowed statuses and HTTP status code.
    """

    options = status_query_service.list_allowed_statuses()
    return {"statuses": options}, 200


@user_bp.get("/status/history")
@login_required_view
def get_status_history() -> tuple[dict[str, object], int]:
    """Returns the authenticated user's phone status history.

    Returns:
        tuple[dict[str, object], int]: Status history payload and
            HTTP status code.
    """

    history = status_query_service.list_statuses(cast(User, current_user))
    return {"status_history": history}, 200
