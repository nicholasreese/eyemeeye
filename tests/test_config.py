"""Unit tests for application configuration helpers."""

from __future__ import annotations

import pytest

from src.app.config import AppConfig, load_config


def test_app_config_rejects_short_secret_key() -> None:
    """AppConfig should reject secrets shorter than 16 characters."""

    with pytest.raises(ValueError, match="SECRET_KEY"):
        AppConfig(secret_key="short-key", database_uri="sqlite:///app.db")


def test_app_config_rejects_missing_database_uri() -> None:
    """AppConfig should reject empty database URIs."""

    with pytest.raises(ValueError, match="DATABASE_URI"):
        AppConfig(secret_key="long-secret-key-123", database_uri="")


def test_load_config_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """load_config should read configuration values from environment variables."""

    monkeypatch.setenv("SECRET_KEY", "env-secret-key-123456")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///env.db")
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("RATE_LIMIT", "50/hour")
    monkeypatch.setenv("ENABLE_HTTPS", "true")
    monkeypatch.setenv("TESTING", "true")

    config = load_config()

    assert config.secret_key == "env-secret-key-123456"
    assert config.database_uri == "sqlite:///env.db"
    assert config.environment == "production"
    assert config.rate_limit == "50/hour"
    assert config.enable_https is True
    assert config.testing is True
