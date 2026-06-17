"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from flask import Flask
from flask.testing import FlaskClient


def _ensure_src_on_path() -> None:
    """Ensure the project's ``src`` directory is discoverable.

    Args:
        None

    Returns:
        None: This helper only mutates ``sys.path`` when required.
    """

    root_path = Path(__file__).resolve().parents[1]
    root_path_str = str(root_path)
    if root_path_str not in sys.path:
        sys.path.insert(0, root_path_str)


_ensure_src_on_path()


@pytest.fixture()
def app() -> Iterator[Flask]:
    """Create and configure a Flask application for testing.

    Args:
        None

    Returns:
        Iterator[Flask]: A configured Flask application instance.
    """

    _ensure_src_on_path()

    from src.app import create_app
    from src.app.config import AppConfig
    from src.app.extensions import db

    config = AppConfig(
        secret_key="super-secret-key-1234",
        database_uri="sqlite:///:memory:",
        environment="testing",
        rate_limit="100/hour",
        enable_https=False,
        testing=True,
    )
    flask_app = create_app(config)
    yield flask_app
    with flask_app.app_context():
        db.drop_all()


@pytest.fixture()
def client(app: Flask) -> FlaskClient:
    """Provide a Flask test client for API interaction.

    Args:
        app (Flask): The Flask application returned by the ``app`` fixture.

    Returns:
        FlaskClient: A test client for invoking HTTP calls.
    """

    return app.test_client()
