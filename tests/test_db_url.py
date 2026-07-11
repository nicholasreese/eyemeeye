"""Tests for build_database_url — URL construction, dialect rewriting, and password encoding."""

from __future__ import annotations

import configparser

import pytest

from src.app.utils.db_url import build_database_url


BASE = "postgresql+psycopg://user@db:5432/mydb"
BASE_BARE = "postgresql://user@db:5432/mydb"


class TestDialectRewrite:
    def test_bare_postgresql_becomes_psycopg(self) -> None:
        assert build_database_url(BASE_BARE).startswith("postgresql+psycopg://")

    def test_already_psycopg_unchanged(self) -> None:
        result = build_database_url(BASE)
        assert result == BASE

    def test_sqlite_unchanged(self) -> None:
        url = "sqlite:///app.db"
        assert build_database_url(url) == url

    def test_non_postgresql_unchanged(self) -> None:
        url = "mysql+pymysql://user@host/db"
        assert build_database_url(url) == url


class TestPasswordInjection:
    def test_no_password_returns_base_url(self) -> None:
        assert build_database_url(BASE, "") == BASE

    def test_simple_password_injected(self) -> None:
        result = build_database_url(BASE, "simple")
        assert "simple@db" in result

    def test_at_sign_in_password_encoded(self) -> None:
        result = build_database_url(BASE, "p@ss")
        assert "p@ss" not in result
        assert "%40" in result

    def test_hash_in_password_encoded(self) -> None:
        result = build_database_url(BASE, "p#ss")
        assert "#" not in result
        assert "%23" in result

    def test_dollar_in_password_encoded(self) -> None:
        result = build_database_url(BASE, "p$ss")
        assert "$" not in result
        assert "%24" in result

    def test_percent_in_password_encoded(self) -> None:
        result = build_database_url(BASE, "50%off")
        assert "50%off" not in result
        assert "%25" in result

    def test_complex_password_hostname_survives(self) -> None:
        result = build_database_url(BASE, "M@l$h1@#")
        assert "@db:5432" in result, "hostname must still be 'db'"
        assert result.endswith("/mydb")

    def test_existing_password_not_overwritten(self) -> None:
        url_with_pass = "postgresql+psycopg://user:existing@db:5432/mydb"
        result = build_database_url(url_with_pass, "other")
        assert "existing" in result
        assert "other" not in result

    def test_bare_dialect_plus_special_password(self) -> None:
        result = build_database_url(BASE_BARE, "p@ss#1")
        assert result.startswith("postgresql+psycopg://")
        assert "@db:5432" in result


class TestConfigParserCompatibility:
    """Regression: set_main_option uses ConfigParser which rejects bare % in values."""

    def test_plain_url_accepted_by_configparser(self) -> None:
        result = build_database_url(BASE, "simplepass")
        cfg = configparser.ConfigParser()
        cfg.add_section("alembic")
        cfg.set("alembic", "sqlalchemy.url", result)  # must not raise

    def test_percent_encoded_url_rejected_by_configparser(self) -> None:
        """Documents why set_main_option must not be used with encoded passwords."""
        encoded = build_database_url(BASE, "p@ss#1")
        assert "%" in encoded
        cfg = configparser.ConfigParser()
        cfg.add_section("alembic")
        with pytest.raises(ValueError, match="invalid interpolation syntax"):
            cfg.set("alembic", "sqlalchemy.url", encoded)
