"""Helper utilities for consistent API responses."""

from __future__ import annotations


def error_response(message: str, status_code: int) -> tuple[dict[str, object], int]:
    """Constructs an error response payload.

    Args:
        message (str): Error message to include in the response.
        status_code (int): HTTP status code representing the error.

    Returns:
        tuple[dict[str, object], int]: Error payload and HTTP status code.
    """

    return {"message": message}, status_code


def validation_error_response(message: str) -> tuple[dict[str, object], int]:
    """Constructs a validation error response payload.

    Args:
        message (str): Validation error message to include in the response.

    Returns:
        tuple[dict[str, object], int]: Error payload and HTTP 400 status code.
    """

    return error_response(message, 400)
