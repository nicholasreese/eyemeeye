"""Unit tests for API response helpers."""

from __future__ import annotations

from src.app.routes.responses import error_response, validation_error_response


def test_error_response_returns_payload_and_status() -> None:
    """error_response should return message and status code."""

    payload, status = error_response("Something went wrong", 500)

    assert payload == {"message": "Something went wrong"}
    assert status == 500


def test_validation_error_response_returns_400() -> None:
    """validation_error_response should return HTTP 400 errors."""

    payload, status = validation_error_response("Invalid input")

    assert payload == {"message": "Invalid input"}
    assert status == 400
